from fastapi import FastAPI, Request, Depends, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Optional, List
from PIL import Image
import io
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime
import os
import time
import asyncio
from sqlalchemy import MetaData, create_engine, Column, String, Table, inspect, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import stripe
import boto3
import re
import string
from pathlib import Path
from dotenv import load_dotenv
import cv2
import numpy as np
from pprint import pprint
from pdfrw import PdfReader
from fillpdf import fillpdfs
import subprocess
import os
import PyPDF2
from pdf2image import convert_from_path
from reportlab.pdfgen import canvas
import glob
import google.oauth2.credentials
import google_auth_oauthlib.flow

Base = declarative_base()
load_dotenv()


class S3():
    def __init__(self):
        self.AWS_ACCESS_ID = os.getenv('AWS_ACCESS_ID')
        self.AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
        self.s3 = boto3.client('s3', aws_access_key_id=self.AWS_ACCESS_ID,
                               aws_secret_access_key=self.AWS_SECRET_KEY)
        self.bucket_name = "doloreschatbucket"
        self.session = boto3.Session(
            aws_access_key_id=self.AWS_ACCESS_ID, aws_secret_access_key=self.AWS_SECRET_KEY)
        self.bucket_s3 = self.session.resource('s3')
        self.bucket = self.bucket_s3.Bucket(self.bucket_name)

    def resizeThumbnail(self, image, resize):
        min_dimension = min(image.width, image.height)
        resize_factor = resize[0] / min_dimension
        new_width = int(image.width * resize_factor)
        new_height = int(image.height * resize_factor)
        resized_image = image.resize(
            (new_width, new_height), Image.Resampling.LANCZOS)
        left = (resized_image.width - resize[0]) / 2
        top = (resized_image.height - resize[1]) / 2
        cropped_image = resized_image.crop(
            (left, top, left + resize[0], top + resize[1]))
        return cropped_image

    def upload_newPic(self, file, directory):
        profilePic_dir = f"{directory}/profilePic/"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=f"{profilePic_dir}user.png",
            Body=file,
        )

    def upload_files(self, file_path, file_dir):
        self.s3.upload_file(
            file_path,
            self.bucket_name,
            file_dir,
        )
        return f'https://doloreschatbucket.s3.us-east-2.amazonaws.com/{file_dir}'

    def getLegalName(self, filename):
        legal_chars = set(string.ascii_letters + string.digits + '._-')
        cleaned_filename = ''.join(c for c in filename if c in legal_chars)
        cleaned_filename = re.sub(r'\.+', '.', cleaned_filename)
        cleaned_filename = cleaned_filename.strip('. ')
        if not cleaned_filename:
            cleaned_filename = 'file'
        max_length = 255
        if len(cleaned_filename) > max_length:
            cleaned_filename = cleaned_filename[:max_length]
        return cleaned_filename

    def s3_headObj(self, s3_key):
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except:
            return False

    def checkfile(self, destination_dir, filename):
        counter = 1
        s3_key = f"{destination_dir}/{filename}"
        while self.s3_headObj(s3_key):
            stem, ext = os.path.splitext(filename)
            mod_filename = f"{stem}_{counter}{ext}"
            counter += 1
            s3_key = f"{destination_dir}/{mod_filename}"
        return s3_key

    def renameDir(self, oldname, newname):
        for obj in self.bucket.objects.filter(Prefix=oldname):
            old_source = {'Bucket': self.bucket_name, 'Key': obj.key}
            new_key = obj.key.replace(oldname, newname, 1)
            new_obj = self.bucket.Object(new_key)
            new_obj.copy(old_source)

        for obj in self.bucket.objects.filter(Prefix=oldname):
            self.bucket_s3.Object(self.bucket_name, obj.key).delete()

    def createDir(self, username):
        newFolders = [f'users/{username}/profilePic/',
                      f'users/{username}/files/', f'users/{username}/forms/', f'users/{username}/filledForms/']
        for folder in newFolders:
            self.bucket.put_object(Key=folder, Body=b'')


class formFiller():
    def __init__(self, pdf_path='i589_template.pdf'):
        with open('keyMap.json', 'r') as keyMap:
            self.key_mapping = json.load(keyMap)
        with open('webForm.json', 'r') as webForm:
            tempDict = json.load(webForm)
        self.web_form_data = {int(k): v for k,v in tempDict.items()}
        self.pdf_path = pdf_path
        self.i589_form = PdfReader(pdf_path)
        self.fieldDets = {}
        self.fieldKeys = []
        fields = self.i589_form.Root.AcroForm.Fields
        for field in fields:
            fieldfont = f'(/Helv 9 Tf 0 0 0 rg)'
            if field.FT == "/Btn":
                fieldkey = field['/T'][1:-1]
                fieldtype = 'checkbox'
                fieldrect = [int(coor) for coor in field['/Kids'][0]['/Rect']]
                fieldOpts = list(field['/Kids'][0]['/AP']['/D'].keys())
            else:
                fieldOpts = []
                fieldkey = field['/T'][1:-1]
                fieldrect = [int(coor) for coor in field['/Kids'][0]['/Rect']]
                if abs(fieldrect[1]-fieldrect[3]) > 16:
                    if 'sign' in fieldkey:
                        fieldtype = 'sign'
                    else:
                        fieldtype = 'textarea'
                else:
                    fieldtype = 'text'

            if fieldtype not in self.fieldDets:
                self.fieldDets[fieldtype] = [
                    [fieldkey, fieldrect, fieldOpts, fieldfont]]
            else:
                self.fieldDets[fieldtype].append(
                    [fieldkey, fieldrect, fieldOpts, fieldfont])

        for type in self.fieldDets:
            for detail in self.fieldDets[type]:
                self.fieldKeys.append(detail[0])
        self.numKeys = len(self.fieldKeys)

    def transfer_data(self, web_form_data, physical_form_data={}):
        suppB = {}
        unnecessary = []

        for key_val in web_form_data:
            web_key = web_form_data[key_val][0]
            web_value = web_form_data[key_val][1]
            physical_key = self.key_mapping[key_val][1]
            if '-' == physical_key:
                suppB[web_key] = web_value

            if 'suppAB' in web_key:
                keys = physical_key.split(' | ')
                for keySuppAB in keys:
                    physical_form_data[keySuppAB] = web_value

            elif type(web_value) == list:
                if '|' in physical_key:
                    phyKeys = physical_key.split(' | ')
                    for keyVal in web_value:
                        for keyTemp in phyKeys:
                            if keyVal in keyTemp:
                                physical_form_data[keyTemp] = keyVal

            elif '|' in physical_key:
                keys = physical_key.split(' | ')
                for key in keys:
                    if web_value in key.lower():
                        if 'male' in web_value:
                            if f'_{web_value}' in key or web_value.capitalize() in key:
                                try:
                                    physical_form_data[key] = web_value
                                except:
                                    physical_form_data[key] += ''
                            else:
                                unnecessary.append(key)
                        else:
                            physical_form_data[key] = web_value
                    elif 'include' in key.lower():
                        if 'yes' in web_value:
                            if '_include' in key or 'eInclude' in key:
                                physical_form_data[key] = web_value
                        else:
                            if '_notinclude' in key or 'NInclude' in key:
                                physical_form_data[key] = web_value
                    elif 'US' in key:
                        if 'yes' in [web_value]:
                            if 'nUS' in key:
                                physical_form_data[key] = web_value
                        else:
                            if 'tUS' in [web_value]:
                                physical_form_data[key] = web_value
            else:
                if physical_key not in physical_form_data:
                    physical_form_data[physical_key] = web_value
                else:
                    newValue = f'{physical_form_data[physical_key]}\n{web_value}'
                    physical_form_data[physical_key] = newValue

        return physical_form_data, suppB, unnecessary

    def createSign(self, signFile):
        signature_org = cv2.imread(signFile)
        split_img = cv2.split(signature_org)
        binary_sig = np.full_like(split_img[0], 255)
        for color_channel in split_img[:3]:
            binary_sig = cv2.bitwise_and(binary_sig, cv2.threshold(
                color_channel, 127, 255, cv2.THRESH_OTSU)[1])
        blur_amount = 5
        blur_binary_sig = cv2.medianBlur(binary_sig, blur_amount)
        trans_sig = cv2.cvtColor(blur_binary_sig, cv2.COLOR_GRAY2BGRA)
        alpha_channel = 255 - blur_binary_sig
        trans_sig[:, :, 3] = alpha_channel
        gray = cv2.cvtColor(trans_sig, cv2.COLOR_BGRA2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        kernel = np.ones((51, 51), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        largest_contour = max(contours, key=cv2.contourArea)
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [largest_contour], 0, 255, -1)
        masked_image = cv2.bitwise_and(
            trans_sig, trans_sig, mask=mask)[:, :, 3]
        x, y, w, h = cv2.boundingRect(mask)
        pil_image = Image.fromarray(masked_image)
        cropped_image = pil_image.crop((x, y, x+w, y+h))
        saveFile = np.array(cropped_image)
        saveFile = cv2.bitwise_not(saveFile)
        if cropped_image.mode == 'RGB':
            saveFile = saveFile[:, :, ::-1].copy()
        return saveFile

    def flattenPDF(self, inputPath, outputPath=None):
        if not outputPath:
            outputPath = inputPath
        subprocess.run(["pdfcrop", "--margins", "0", inputPath, outputPath])

    def signPDF(self, signature_info, filename='./i589_flat.pdf'):
        file_name = os.path.basename(filename)
        file_name_without_extension = os.path.splitext(file_name)[0]
        temp_path = "./temp"
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        with open(filename, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            page_width = pdf_reader.pages[0].mediabox.width
            page_height = pdf_reader.pages[0].mediabox.height
            for page_num in range(len(pdf_reader.pages)):
                writer = PyPDF2.PdfWriter()
                writer.add_page(pdf_reader.pages[page_num])
                output_filename = temp_path + '/' + \
                    file_name_without_extension + \
                    '_page_' + str(page_num) + '.pdf'
                with open(output_filename, 'wb') as out:
                    writer.write(out)
        for sig_info in signature_info:
            cv_signature = self.createSign(sig_info[0])
            page = sig_info[1]
            offset_xy = sig_info[2]
            page_to_be_signed = temp_path + '/' + \
                file_name_without_extension + '_page_' + str(page-1)
            images = convert_from_path(page_to_be_signed + '.pdf')
            images[0].save(page_to_be_signed + '.jpg', 'JPEG')
            cv_page = cv2.imread(page_to_be_signed + '.jpg')
            scale = 1
            if cv_signature.shape[0] > cv_page.shape[0] or cv_signature.shape[1] > cv_page.shape[1]:
                scale_min = min(
                    cv_page.shape[0]/cv_signature.shape[0], cv_page.shape[1]/cv_signature.shape[1])
                if scale > scale_min:
                    scale = scale_min
            indices = np.where(cv_signature == 0)
            signature_coords = np.transpose(indices)
            signature_coords = signature_coords * scale
            offset_x_pos = cv_page.shape[0] - cv_signature.shape[0] * scale
            offset_y_pos = cv_page.shape[1] - cv_signature.shape[1] * scale
            signature_coords = signature_coords + \
                [offset_x_pos * offset_xy[0], offset_y_pos * offset_xy[1]]
            for coord in signature_coords:
                cv_page[int(coord[0]), int(coord[1])] = 0
            cv2.imwrite(page_to_be_signed + '.jpg', cv_page)
            c = canvas.Canvas(page_to_be_signed + '.pdf',
                              pagesize=(page_width, page_height))
            c.drawImage(page_to_be_signed + '.jpg', 0, 0,
                        float(page_width), float(page_height))
            c.save()
        output_pdf = PyPDF2.PdfWriter()
        for i in range(len(pdf_reader.pages)):
            pdf_file = open(
                temp_path + '/' + file_name_without_extension + '_page_' + str(i) + '.pdf', 'rb')
            input_pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in range(len(input_pdf_reader.pages)):
                output_pdf.add_page(input_pdf_reader.pages[page])
            pdf_file.close()
        output_path = './i589_signed.pdf'
        with open(output_path, 'wb') as output_file:
            output_pdf.write(output_file)
        files = glob.glob('temp/*')
        for f in files:
            os.remove(f)

    def main(self, frontend_resp, sign):
        data_dict = {}
        for types in self.fieldDets:
            if types != 'sign':
                for keys in frontend_resp:
                    for detail in self.fieldDets[types]:
                        if keys == detail[0]:
                            data_dict[keys] = frontend_resp[keys]
        fillpdfs.write_fillable_pdf(
            './i589_template.pdf', './i589_filled.pdf', data_dict)
        fillpdfs.flatten_pdf(
            './i589_filled.pdf', './i589_flat.pdf', as_images=True)
        signInfo = [[sign, frontend_resp[keys][0], frontend_resp[keys][1]]
                    for keys in frontend_resp if 'sign' in keys]
        self.signPDF(signInfo)
        os.remove('./i589_filled.pdf')
        os.remove('./i589_flat.pdf')


class User(Base):
    __tablename__ = 'users'

    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, primary_key=True, nullable=False)
    subscription_type = Column(String, default='free', nullable=False)
    username = Column(String, nullable=False)
    location = Column(String)
    profile_pic = Column(
        String, default='https://doloreschatbucket.s3.us-east-2.amazonaws.com/icons/users/user.png', nullable=False)
    password = Column(String)

class GoogleLogin():
    def __init__(self):
        self.CLIENT_ID = os.getenv('CLIENT_ID')
        self.CLIENT_SECRET = os.getenv('CLIENT_SECRET')
        self.oauth2_flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            "client_secret.json",
            scopes=["openid", "email", "profile"]
        )

class Dolores():
    def __init__(self):
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.RELO_ASSISTANT_ID = os.getenv('RELO_ASSISTANT_ID')
        self.DOLORES_ASSISTANT_ID = os.getenv('DOLORES_ASSISTANT_ID')
        self.FORM_ASSISTANT_ID = os.getenv('FORM_ASSISTANT_ID')
        self.context = {
            "user": '',
            "assistant": ''
        }
        self.user_input = ''
        self.bot_response = ''
        self.location = './context/'
        with open('navigateDict.json', 'r') as nav:
            self.webForm = json.load(nav)

    def getFileName(self, user):
        if user == 'unknown':
            contextFile = os.listdir('./context/unknown/')
            now = int(time.time())
            if len(contextFile) > 0:
                if now - int(contextFile[0][:-5]) > 1800 and contextFile[0][-4:] == 'json':
                    os.remove(f'./context/unknown/{contextFile[0]}')
                else:
                    now = contextFile[0][:-5]
            else:
                pass
            return now
        return int(datetime.today().strftime('%Y%m%d'))

    def assistant(self, user_input, assistant='relo'):
        assistant_id = {
            'relo': self.RELO_ASSISTANT_ID,
            'dolores': self.DOLORES_ASSISTANT_ID,
            'form': self.FORM_ASSISTANT_ID
        }
        client = OpenAI(api_key=self.OPENAI_API_KEY)
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"This is the previous context:\n\nuser:{self.context['user']}\nassistant:{self.context['assistant']}. And this is the current prompt: {user_input}. Respond in plain string format, no special formatting",
                }
            ]
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id[assistant]
        )
        while run.status != "completed" and run.status != "requires_action":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        return messages.data[0].content[0].text.value

    def generateContext(self, input, role):
        summarizing_client = OpenAI(api_key=self.OPENAI_API_KEY)
        response = summarizing_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You'll be given a transcript of one of the person in the chat. this transcript is from the {role}. The transcript will have 2 paragraphs, first paragraph will have all the summarized info from previous message sent by the {role} and current message sent by the {role}. You have to summarize both these messages and create a paragraph that will have all the important information from the transcripts. Return summary in this format: 'Previous Context: [summary]'"
                },
                {
                    "role": "user",
                    "content": f"{input}"
                }
            ],
            temperature=0.7,
            top_p=1
        )
        return response.choices[0].message.content

    def openJSON(self, user):
        filename = self.getFileName(user)
        if not os.path.isdir(f"./context/{user}"):
            os.makedirs(f"./context/{user}")
        self.location = f"./context/{user}/{filename}.json"
        try:
            with open(self.location, 'r') as cFile:
                self.context = json.load(cFile)
        except:
            pass

    def saveJSON(self):
        with open(self.location, 'w') as cFile:
            json.dump(self.context, cFile)

    async def chat(self, user_input, user, assistant='relo'):
        self.user_input = user_input
        if assistant == 'form':
            newUserInp = f'help me identify this query, if it is a query related to finding something in the form or going to certain part of the form, then respond with just "1" but if it related to getting help, or questions about parts of the form, respond with "0": "{user_input}"'
            flag = self.assistant(newUserInp, assistant)
            # print(flag)
            if bool(int(flag)):
                response = self.assistant(f'These are the sections and the subsections/questions from the form {self.webForm}. The keys of this dictionary represent the parts of the form, if the value for these keys is a list of dictionaries, then the keys of that dictionary are the sections of the part and their values are the questions in that section, if instead of a list of dictionaries, its a list of strings, then it will contain the question of that part, the sections and the questions are the same in this case, so the <question> will be the same as the <section>. Find the part of the webform based on this query: "{user_input}". respond with just this type of statement "navigate to <part> part of the <section> section. do not add anything else/sources.', assistant)
                self.bot_response = response
        else:
            self.openJSON(user)
            response = self.assistant(user_input, assistant).replace("\n", "<br>")
            self.bot_response = response
        return response

    async def updateContext(self):
        self.context['user'] = self.generateContext(
            f"{self.context['user']}\n\n{self.user_input}", "user")
        self.context['assistant'] = self.generateContext(
            f"{self.context['assistant']}\n\n{self.bot_response}", "assistant")
        self.saveJSON()


class Database():
    def __init__(self):
        self.DB_HOST = os.getenv('DB_HOST')
        self.DB_PORT = os.getenv('DB_PORT')
        self.DB_NAME = os.getenv('DB_NAME')
        self.DB_USER = os.getenv('DB_USER')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD')
        self.database_url = f'postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def createTable(self, username):
        inspector = inspect(self.engine)
        if not inspector.has_table(username.lower()):
            metadata = MetaData()
            new_table = Table(
                username.lower(),
                metadata,
                Column('user_messages', String),
                Column('bot_messages', String),
                Column('files', String),
                Column('forms', String)
            )
            metadata.create_all(self.engine)

    def add_user(self, details, db):
        if details['user_location'] != '':
            location = details['user_location']
        else:
            location = None
        if details['password'] != '':
            password = details['password']
        else:
            password = None

        self.createTable(details['username'])
        new_user = User(first_name=details['firstName'], last_name=details['lastName'], email=details['email'],
                        username=details['username'], profile_pic=details['profilePic'], password=password, location=location)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    def renameTable(self, oldname, newname):
        inspector = inspect(self.engine)
        if inspector.has_table(oldname.lower()):
            rename_query = text(
                f"ALTER TABLE {oldname.lower()} RENAME TO {newname.lower()}")
            with self.engine.begin() as conn:
                conn.execute(rename_query)

    def update_subscription(self, email, tier, db):
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.subscription_type = tier
            db.commit()
            db.refresh(user)

    def add_messages(self, username, user_message, bot_message):
        with self.engine.begin() as conn:
            insert_vals = f"INSERT INTO {username.lower()} (user_messages, bot_messages) VALUES (:user_message, :bot_message)"
            conn.execute(text(insert_vals), {
                         "user_message": user_message, "bot_message": bot_message})

    def add_files(self, username, flag, file_link):
        with self.engine.begin() as conn:
            insert_vals = f"INSERT INTO {username.lower()} ({flag}) VALUES (:file_link)"
            conn.execute(text(insert_vals), {"file_link": file_link})

    def get_files(self, username, flag):
        with self.engine.begin() as conn:
            query = f"SELECT {flag} from {username.lower()}"
            result = conn.execute(text(query))
        files = [row[0] for row in result if row[0] is not None]
        return files

    def free_limit(self, username):
        query = text(
            f"SELECT COUNT(user_messages) AS non_null_count FROM {username.lower()} WHERE user_messages IS NOT NULL;")
        with self.engine.connect() as conn:
            result = conn.execute(query)
            non_null_count = result.scalar()
        return non_null_count


class Stripe():
    def __init__(self) -> None:
        self.publishableKey = os.getenv('publishableKey')
        self.secretKey = os.getenv('secretKey')
        stripe.api_key = self.secretKey
        self.priceID = {
            'basic': {'monthly': 'price_1PGqbSP6cNlgDSsmJ8eZ9R8F', 'yearly': 'price_1PEJ0GP6cNlgDSsmNmInXFzC'},
            'plus': {'monthly': 'price_1PHT38P6cNlgDSsm6Y7TXywW', 'yearly': 'price_1PHT3YP6cNlgDSsmZmLFLpsK'},
            'premium': {'monthly': 'price_1PGkXdP6cNlgDSsmedxP1cEU', 'yearly': 'price_1PGkYCP6cNlgDSsmJfN7djSg'}
        }
        self.tier = 'free'
        self.email = 'none'
        self.transaction_id = 'none'
        self.sessID = 'none'

    def checkOutSess(self, tier, duration, email):
        self.tier = tier
        self.email = email
        subscriptionData = {
            "trial_settings": {"end_behavior": {"missing_payment_method": "pause"}},
            "trial_period_days": 3,
        }
        # subscriptionData={}
        checkoutSess = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': self.priceID[tier][duration],
                    'quantity': 1,
                },
            ],
            subscription_data=subscriptionData,
            mode='subscription',
            success_url='https://justi.guide/success.html',
            cancel_url='https://justi.guide/error.html',
        )
        return checkoutSess.id

    def getTier(self):
        return self.tier

    def getEmail(self):
        return self.email


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot_responses = Dolores()
sql_db = Database()
stripeObj = Stripe()
s3 = S3()
ff = formFiller()
googleLogin = GoogleLogin()


@app.post("/get_response/")
async def get_bot_response(request: Request):
    data = await request.json()
    user_message = data["user_message"]
    user = data["user"]
    assistant = data['assistant']
    bot_response = await bot_responses.chat(user_message, user, assistant)
    sql_db.add_messages(user, user_message, bot_response)
    response = {"bot_response": bot_response}
    asyncio.create_task(bot_responses.updateContext())
    return response


@app.post('/new_user/')
async def new_user(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    user = db.query(User).filter(User.email == data['email']).first()
    if not user:
        s3.createDir(data['username'])
        sql_db.add_user(data, db)
    else:
        sql_db.createTable(data['username'])


@app.post('/create_checkoutsess/')
async def create_checkoutSessID(request: Request):
    data = await request.json()
    coSess_ID = stripeObj.checkOutSess(
        data['tier'], data['duration'], data['email'])
    return {'id': coSess_ID}


@app.post('/stripe-webhook/')
def handle_stripeWebhook(request):
    signature = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            payload=request.get_data(as_text=True),
            sig_header=signature,
            secret=stripe.api_key
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid Signature', 400


@app.get("/update_subscription/")
async def userUpdate(db: Session = Depends(sql_db.get_db)):
    email = stripeObj.getEmail()
    tier = stripeObj.getTier()
    sql_db.update_subscription(email, tier, db)


@app.post('/user_sub/')
async def update_userPage(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    email = data['email']
    user = db.query(User).filter(User.email == email).first()
    if user:
        subscription_tier = user.subscription_type
        return {'subscription': subscription_tier.capitalize()}


@app.post('/check_user/')
async def checkUser(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    email = data['email']
    user = db.query(User).filter(User.email == email).first()
    if user:
        if user.password is not None:
            return {'exists': True}
        else:
            return {'exists': False}
    else:
        return {'exists': False}


@app.post('/register/')
async def registerUser(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    user = db.query(User).filter(User.email == data['email']).first()
    s3.createDir(data['username'])
    if user:
        user.profile_pic = data['profilePic']
        user.first_name = data['firstName']
        user.last_name = data['lastName']
        user.username = data['username']
        user.location = data['user_location']
        user.password = data['password']
        db.commit()
        db.refresh(user)
    else:
        sql_db.add_user(data, db)


@app.post('/check_login/')
async def getPassword(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    user = db.query(User).filter(User.email == data['email']).first()
    if user:
        if user.password != data['password']:
            return {'resp': 'Incorrect Password'}
        else:
            print(user.email)
            return {'resp': True,
                    'username': user.username,
                    'firstName': user.first_name,
                    'lastName': user.last_name,
                    'email': user.email,
                    'profilePicUrl': user.profile_pic,
                    'user_location': user.location}


@app.post('/check_username/')
async def checkUsername(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    user = db.query(User).filter(User.username == data['username']).first()
    if user:
        return {'exists': True}
    else:
        return {'exists': False}


@app.post('/update_user/')
async def updateUser(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    user = db.query(User).filter(User.email == data['email_id']).first()
    oldname = f'users/{user.username}/'
    newname = f"users/{data['username']}/"
    if oldname != newname:
        s3.renameDir(oldname, newname)
        sql_db.renameTable(user.username, data['username'])
    user.username = data['username']
    user.first_name = data['firstName']
    user.last_name = data['lastName']
    user.location = data['user_location']
    user.profile_pic = data['profilePicUrl']
    db.commit()
    db.refresh(user)


@app.post('/update_password/')
async def updatePass(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    user = db.query(User).filter(User.email == data['email_id']).first()
    user.password = data['password']
    db.commit()
    db.refresh(user)


@app.post('/uploadProfilePic/')
async def uploadProfilePic(profilePic: UploadFile = File(...), email_id: str = Form(...), db: Session = Depends(sql_db.get_db)):
    try:
        file_data = await profilePic.read()
        user = db.query(User).filter(User.email == email_id).first()
        user_dir = f"users/{user.username}"
        image = Image.open(io.BytesIO(file_data))
        cropped_image = s3.resizeThumbnail(image, (175, 175))
        png_data = io.BytesIO()
        cropped_image.save(png_data, format='PNG')
        png_data.seek(0)
        s3.upload_newPic(png_data, user_dir)
        return {'resp': True,
                'url': f'https://doloreschatbucket.s3.us-east-2.amazonaws.com/users/{user.username}/profilePic/user.png'}
    except Exception as e:
        return {'resp': False,
                'error': str(e)}


@app.post('/upload_files/')
async def upload_forms(files: List[UploadFile] = File(...), email_id: str = Form(...), flag: str = Form(...), db: Session = Depends(sql_db.get_db)):
    user = db.query(User).filter(User.email == email_id).first()
    destination_dir = f"users/{user.username}/{flag}"
    for file in files:
        tmp_filename = s3.getLegalName(file.filename)
        temp_file_path = Path('/tmp') / tmp_filename
        temp_file_path.parent.mkdir(parents=True, exist_ok=True)
        s3_key = s3.checkfile(destination_dir, tmp_filename)
        with open(temp_file_path, 'wb') as temp_file:
            content = await file.read()
            temp_file.write(content)

        file_url = s3.upload_files(str(temp_file_path), s3_key)
        sql_db.add_files(user.username, flag, file_url)
        os.remove(str(temp_file_path))


@app.post('/get_filesList/')
async def get_filesList(email_id: str = Form(...), flag: str = Form(...), db: Session = Depends(sql_db.get_db)):
    standard_iconPack = {
        'mp3': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/audio.svg",
        'wav': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/audio.svg",
        'aac': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/audio.svg",
        'flac': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/audio.svg",
        'txt': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/doc.svg",
        'doc': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/doc.svg",
        'docx': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/doc.svg",
        'rtf': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/doc.svg",
        'odt': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/doc.svg",
        'xlsx': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/spreadsheet.svg",
        'xls': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/spreadsheet.svg",
        'ods': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/spreadsheet.svg",
        'csv': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/spreadsheet.svg",
        'tsv': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/spreadsheet.svg",
        'jpeg': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/image.svg",
        'jpg': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/image.svg",
        'png': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/image.svg",
        'gif': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/image.svg",
        'bmp': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/image.svg",
        'tiff': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/image.svg",
        'svg': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/image.svg",
        'pdf': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/pdf.svg",
        'pptx': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/presentation.svg",
        'ppt': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/presentation.svg",
        'odp': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/presentation.svg",
        'mp4': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/video.svg",
        'avi': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/video.svg",
        'mov': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/video.svg",
        'flv': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/video.svg",
        'wmv': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/video.svg",
        'mkv': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/video.svg",
        'zip': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/zip.svg",
        'rar': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/zip.svg",
        '7z': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/zip.svg",
        'gz': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/zip.svg",
        'tar': "https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/zip.svg"
    }
    unknownType = 'https://doloreschatbucket.s3.us-east-2.amazonaws.com/file_icons/unknown.svg'
    user = db.query(User).filter(User.email == email_id).first()
    tablename = user.username
    fileList = sql_db.get_files(tablename, flag)
    if len(fileList) > 0:
        thumbnails = [standard_iconPack.get(file.split(
            '.')[-1], unknownType) for file in fileList]
        filenames = [file.split('/')[-1] for file in fileList]
        output_dic = [
            {'title': title, 'url': url, 'thumbnail': thumbnail}
            for title, url, thumbnail in zip(filenames, fileList, thumbnails)
        ]
        return JSONResponse(output_dic)
    else:
        return []


@app.post('/free_chatLimit/')
async def free_chatLimit(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    email_id = data['email_id']
    user = db.query(User).filter(User.email == email_id).first()
    num_messages = sql_db.free_limit(user.username)
    if num_messages is not None and num_messages >= 4:
        return {'result': True,
                'num': num_messages}
    else:
        return {'result': False,
                'num': num_messages}


@app.post('/get_profilePic/')
async def getPP(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    user = db.query(User).filter(User.email == data['email_id']).first()
    if user:
        profilePic = user.profile_pic
        if f'{user.username}' in profilePic:
            return {'result': True,
                    'profilePic': profilePic}
    return {'result': False}


@app.post('/get_formData/')
async def getForm(
    email_id: str = Form(...),
    partdhiddenFileInput: Optional[UploadFile] = File(...),
    texts: Optional[str] = Form(...),
    lists: Optional[str] = Form(...),
    db: Session = Depends(sql_db.get_db)
):
    idealSign_map = {
        "d_sign": [9, [0.55, 0.23]],
        "suppA_sign": [11, [0.13, 0.69]],
        "suppB_sign": [12, [0.15, 0.65]],
    }
    sign_map = {
        "d_sign": [9, [0.55, 0.23]]
    }
    text_data = json.loads(texts) if texts else {}
    newTextData = {}
    for keys in text_data:
        ind = [key for key, value in ff.web_form_data.items() if isinstance(
            value, (list, tuple)) and value[0] == keys]
        if len(ind) > 0:
            newTextData[ind[0]] = [keys, text_data[keys]]
    newListData = {}
    currData, _, _ = ff.transfer_data(newTextData)
    list_data = json.loads(lists) if lists else {}
    for list_key in list_data:
        ind = [key for key, value in ff.web_form_data.items() if isinstance(
            value, (list, tuple)) and value[0] == list_key]
        if len(ind) > 0:
            newListData[ind[0]] = [list_key, list_data[list_key]]
    upData, _, _ = ff.transfer_data(newListData, currData)
    content = await partdhiddenFileInput.read()
    with open(f'./temp/{partdhiddenFileInput.filename}', 'wb') as f:
        f.write(content)
    for keyWeb in upData:
        if f'{keyWeb[:5]}_sign' in list(idealSign_map.keys())[1:]:
            sign_map[f'{keyWeb[:5]}_sign'] = idealSign_map[f'{keyWeb[:5]}_sign']
    tempFile = f'./temp/{partdhiddenFileInput.filename}'
    sign_keys = [key for key, value in ff.web_form_data.items() if isinstance(
        value, (list, tuple)) and value[0] == "part-d-hiddenFileInput"]
    for sKey in sign_keys:
        signKey = ff.key_mapping[sKey][1]
        if signKey in sign_map:
            upData[ff.key_mapping[sKey][1]] = sign_map[ff.key_mapping[sKey][1]]
    ff.main(upData, tempFile)
    file = './i589_signed.pdf'
    user = db.query(User).filter(User.email == email_id).first()
    destination_dir = f"users/{user.username}/filledForms"
    tmp_filename = s3.getLegalName(file)
    temp_file_path = Path('./temp') / tmp_filename
    temp_file_path.parent.mkdir(parents=True, exist_ok=True)
    s3_key = f'{destination_dir}/i589_signed.pdf'

    try:
        os.rename(file, temp_file_path)
    except:
        os.replace(file, temp_file_path)
    file_url = s3.upload_files(str(temp_file_path), s3_key)
    destination_dir = f"users/{user.username}/forms"
    tmp_filename = s3.getLegalName(file)
    temp_file_path = Path('./temp') / tmp_filename
    temp_file_path.parent.mkdir(parents=True, exist_ok=True)
    s3_key = s3.checkfile(destination_dir, tmp_filename)
    formUrl = s3.upload_files(str(temp_file_path), s3_key)
    sql_db.add_files(user.username, 'forms', formUrl)
    os.remove(temp_file_path)
    return {"uploaded": file_url}

@app.post("/verify-credential")
async def verify_credential(request: Request):
    try:
        credential = await request.form()["credential"]
        idinfo = google.oauth2.credentials.verify_google_oauth2_token(
            credential, googleLogin.oauth2_flow.client_config["client_id"]
        )
        if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Wrong Issuer.")
        user_info = {
            "email": idinfo["email"],
            "firstName": idinfo["given_name"],
            "lastName": idinfo["family_name"],
            "profilePicUrl": idinfo["picture"],
        }
        return JSONResponse({"success": True, **user_info})
    except ValueError as e:
        return JSONResponse({"success": False, "error": str(e)})



@app.get('/test/')
async def test_func():
    return {'test': 'successful'}

if __name__ == "__main__":
    host = '0.0.0.0'
    uvicorn.run("backend:app", host=host, reload=True)
