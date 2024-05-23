from fastapi import Body, FastAPI, Request, HTTPException, Depends, File, UploadFile, Form
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

Base = declarative_base()


class S3():
    def __init__(self):
        self.AWS_ACCESS_ID = ""
        self.AWS_SECRET_KEY = ""
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
        print('uploading!')
        profilePic_dir = f"{directory}/profilePic/"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=f"{profilePic_dir}user.png",
            Body=file,
        )
        print('uploaded')

    def upload_files(self, file_path, file_dir):
        self.s3.upload_file(
            file_path,
            self.bucket_name,
            file_dir,
        )

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
        # return newname

    def createDir(self, username):
        newFolders = [f'users/{username}/profilePic/',
                      f'users/{username}/files/', f'users/{username}/forms/']
        for folder in newFolders:
            self.bucket.put_object(Key=folder, Body=b'')
        # return username


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


class Dolores():
    def __init__(self):
        self.OPENAI_API_KEY = ""
        self.OPENAI_ASSISTANT_ID = ""
        self.context = {
            "user": '',
            "assistant": ''
        }
        self.user_input = ''
        self.bot_response = ''
        self.location = './context/'

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

    def assistant(self, user_input):
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
            assistant_id=self.OPENAI_ASSISTANT_ID
        )
        while run.status != "completed":
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

    async def chat(self, user_input, user):
        self.user_input = user_input
        self.openJSON(user)
        response = self.assistant(user_input).replace("\n", "<br>")
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
        self.database_url = 'postgresql://dolores:JustiGuide!UserInfo2024@user-details.cf2y80iom48x.us-west-1.rds.amazonaws.com:5432/user_details'
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def add_user(self, details, db):
        if details['user_location'] != '':
            location = details['user_location']
        else:
            location = None
        if details['password'] != '':
            password = details['password']
        else:
            password = None

        inspector = inspect(self.engine)
        if not inspector.has_table(details['username']):
            metadata = MetaData()
            new_table = Table(
                details['username'],
                metadata,
                Column('user_messages', String),
                Column('bot_messages', String),
                Column('files', String),
                Column('forms', String)
            )
            metadata.create_all(self.engine)
        new_user = User(first_name=details['firstName'], last_name=details['lastName'], email=details['email'],
                        username=details['username'], profile_pic=details['profilePic'], password=password, location=location)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    def renameTable(self, oldname, newname):
        inspector = inspect(self.engine)
        if inspector.has_table(oldname):
            rename_query = text(f"ALTER TABLE {oldname} RENAME TO {newname}")
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
            insert_vals = f"INSERT INTO {username} (user_messages, bot_messages) VALUES (:user_message, :bot_message)"
            conn.execute(text(insert_vals), {"user_message": user_message, "bot_message": bot_message})

class Stripe():
    def __init__(self) -> None:
        self.publishableKey = ''
        self.secretKey = ''
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
        checkoutSess = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': self.priceID[tier][duration],
                    'quantity': 1,
                },
            ],
            subscription_data={
                "trial_settings": {"end_behavior": {"missing_payment_method": "pause"}},
                "trial_period_days": 1,
            },
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


@app.post("/get_response/")
async def get_bot_response(request: Request):
    data = await request.json()
    user_message = data["user_message"]
    user = data["user"]
    bot_response = await bot_responses.chat(user_message, user)
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
        print(user.username)
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
async def upload_forms(files: List[UploadFile] = File(...), email_id: str = Form(...), db: Session = Depends(sql_db.get_db)):
    user = db.query(User).filter(User.email == email_id).first()
    destination_dir = f"users/{user.username}/files"
    for file in files:
        tmp_filename = s3.getLegalName(file.filename)
        temp_file_path = Path('/tmp') / tmp_filename
        temp_file_path.parent.mkdir(parents=True, exist_ok=True)
        s3_key = s3.checkfile(destination_dir, tmp_filename)
        with open(temp_file_path, 'wb') as temp_file:
            content = await file.read()
            temp_file.write(content)

        s3.upload_files(str(temp_file_path), s3_key)
        os.remove(str(temp_file_path))


@app.get('/test/')
async def test_func():
    return {'test': 'successful'}

if __name__ == "__main__":
    host = '0.0.0.0'
    uvicorn.run("backend:app", reload=True)
