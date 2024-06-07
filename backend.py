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
        self.key_mapping = [
            ["part-a-i-a-i-aliases", "ai_aliases"],
            ["part-a-i-a-i-anumber", "ai_anumber"],
            ["part-a-i-a-i-apt", "ai_apt"],
            ["part-a-i-a-i-ccob", "ai_country"],
            ["part-a-i-a-i-citizenship", "ai_citizenship"],
            ["part-a-i-a-i-city", "ai_city"],
            ["part-a-i-a-i-currDate", "ai_arrivalDate_1"],
            ["part-a-i-a-i-currExp", "ai_arrivalExpire_1"],
            ["part-a-i-a-i-currPlace", "ai_arrivalPlace_1"],
            ["part-a-i-a-i-currSts", "ai_arrivalStatus_1"],
            ["part-a-i-a-i-date-0", "ai_arrivalDate_2"],
            ["part-a-i-a-i-date-1", "ai_arrivalDate_3"],
            ["part-a-i-a-i-date-2", "-"],
            ["part-a-i-a-i-date-3", "-"],
            ["part-a-i-a-i-date-4", "-"],
            ["part-a-i-a-i-date-5", "-"],
            ["part-a-i-a-i-dob", "ai_dob"],
            ["part-a-i-a-i-expDate", "ai_passportExpire"],
            ["part-a-i-a-i-firstName", "ai_firstName"],
            ["part-a-i-a-i-gender", "ai_male | ai_female"],
            ["part-a-i-a-i-i94", "ai_i94"],
            ["part-a-i-a-i-immiProceedings", "ai_never | ai_now | ai_past"],
            ["part-a-i-a-i-lastName", "ai_lastName"],
            ["part-a-i-a-i-leftDate", "ai_leaveDate"],
            ["part-a-i-a-i-mailApt", "ai_Mailapt"],
            ["part-a-i-a-i-mailCity", "ai_Mailcity"],
            ["part-a-i-a-i-mailCO", "ai_Mailco"],
            ["part-a-i-a-i-mailState", "ai_Mailstate"],
            ["part-a-i-a-i-mailStreet", "ai_Mailstreet"],
            ["part-a-i-a-i-mailTel", "ai_Mailtel"],
            ["part-a-i-a-i-mailZipCode", "ai_MailzipCode"],
            ["part-a-i-a-i-maritalSts",
                "ai_single | ai_married | ai_divorced | ai_widow"],
            ["part-a-i-a-i-middleName", "ai_middleName"],
            ["part-a-i-a-i-nationality", "ai_nationality"],
            ["part-a-i-a-i-nativeLang", "ai_nativeLang"],
            ["part-a-i-a-i-otherFluency", "ai_otherLang"],
            ["part-a-i-a-i-passportInfo", "ai_passportCountry"],
            ["part-a-i-a-i-passportNum", "ai_passportNum"],
            ["part-a-i-a-i-place-0", "ai_arrivalPlace_2"],
            ["part-a-i-a-i-place-1", "ai_arrivalPlace_3"],
            ["part-a-i-a-i-place-2", "-"],
            ["part-a-i-a-i-place-3", "-"],
            ["part-a-i-a-i-place-4", "-"],
            ["part-a-i-a-i-place-5", "-"],
            ["part-a-i-a-i-race", "ai_race"],
            ["part-a-i-a-i-religion", "ai_religion"],
            ["part-a-i-a-i-ssn", "ai_ssn"],
            ["part-a-i-a-i-state", "ai_state"],
            ["part-a-i-a-i-status-0", "ai_arrivalStatus_2"],
            ["part-a-i-a-i-status-1", "ai_arrivalStatus_3"],
            ["part-a-i-a-i-status-2", "-"],
            ["part-a-i-a-i-status-3", "-"],
            ["part-a-i-a-i-status-4", "-"],
            ["part-a-i-a-i-status-5", "-"],
            ["part-a-i-a-i-street", "ai_street"],
            ["part-a-i-a-i-tel", "ai_tel"],
            ["part-a-i-a-i-traveDocNum", "ai_travelDocNum"],
            ["part-a-i-a-i-uscis", "ai_uscis"],
            ["part-a-i-a-i-zipCode", "ai_zipCode"],
            ["part-a-i-eng_fluency", "ai_fluency"],
            ["part-a-ii-a-ii-child-0-anumber", "aii_children_1_anumber"],
            ["part-a-ii-a-ii-child-0-ccob", "aii_children_1_cob"],
            ["part-a-ii-a-ii-child-0-citizenship", "aii_children_1_citizenship"],
            ["part-a-ii-a-ii-child-0-currExp", "aii_children_1_currExp"],
            ["part-a-ii-a-ii-child-0-currSts", "aii_children_1_currSts"],
            ["part-a-ii-a-ii-child-0-dob", "aii_children_1_dob"],
            ["part-a-ii-a-ii-child-0-firstName", "aii_children_1_firstName"],
            ["part-a-ii-a-ii-child-0-gender",
                "aii_children_1_female | aii_children_1_male"],
            ["part-a-ii-a-ii-child-0-i94", "aii_children_1_i94"],
            ["part-a-ii-a-ii-child-0-id", "aii_children_1_ID"],
            ["part-a-ii-a-ii-child-0-immiProc",
                "aii_children_1_inICP | aii_children_1_notICP"],
            ["part-a-ii-a-ii-child-0-inclusion",
                "aii_children_1_include | aii_children_1_notinclude"],
            ["part-a-ii-a-ii-child-0-lastEntry-date",
                "aii_children_1_lastEntry_date"],
            ["part-a-ii-a-ii-child-0-lastEntry-place",
                "aii_children_1_lastEntry_place"],
            ["part-a-ii-a-ii-child-0-lastEntry-status",
                "aii_children_1_lastEntry_sts"],
            ["part-a-ii-a-ii-child-0-lastName", "aii_children_1_lastName"],
            ["part-a-ii-a-ii-child-0-loc", "aii_children_1_loc"],
            ["part-a-ii-a-ii-child-0-maritalSts", "aii_children_1_maritalSts"],
            ["part-a-ii-a-ii-child-0-middleName", "aii_children_1_middleName"],
            ["part-a-ii-a-ii-child-0-race", "aii_children_1_race"],
            ["part-a-ii-a-ii-child-0-ssn", "aii_children_1_ssn"],
            ["part-a-ii-a-ii-child-0-UScheck",
                "aii_children_1_notUS | aii_children_1_inUS"],
            ["part-a-ii-a-ii-child-1-anumber", "aii_children_2_anumber"],
            ["part-a-ii-a-ii-child-1-ccob", "aii_children_2_cob"],
            ["part-a-ii-a-ii-child-1-citizenship", "aii_children_2_citizenship"],
            ["part-a-ii-a-ii-child-1-currExp", "aii_children_2_currExp"],
            ["part-a-ii-a-ii-child-1-currSts", "aii_children_2_currSts"],
            ["part-a-ii-a-ii-child-1-dob", "aii_children_2_dob"],
            ["part-a-ii-a-ii-child-1-firstName", "aii_children_2_firstName"],
            ["part-a-ii-a-ii-child-1-gender",
                "aii_children_2_male | aii_children_2_female"],
            ["part-a-ii-a-ii-child-1-i94", "aii_children_2_i94"],
            ["part-a-ii-a-ii-child-1-id", "aii_children_2_ID"],
            ["part-a-ii-a-ii-child-1-immiProc",
                "aii_children_2_inICP | aii_children_2_notICP"],
            ["part-a-ii-a-ii-child-1-inclusion",
                "aii_children_2_include | aii_children_2_notinclude"],
            ["part-a-ii-a-ii-child-1-lastEntry-date",
                "aii_children_2_lastEntry_date"],
            ["part-a-ii-a-ii-child-1-lastEntry-place",
                "aii_children_2_lastEntry_place"],
            ["part-a-ii-a-ii-child-1-lastEntry-status",
                "aii_children_2_lastEntry_sts"],
            ["part-a-ii-a-ii-child-1-lastName", "aii_children_2_lastName"],
            ["part-a-ii-a-ii-child-1-loc", "aii_children_2_loc"],
            ["part-a-ii-a-ii-child-1-maritalSts", "aii_children_2_maritalSts"],
            ["part-a-ii-a-ii-child-1-middleName", "aii_children_2_middleName"],
            ["part-a-ii-a-ii-child-1-race", "aii_children_2_race"],
            ["part-a-ii-a-ii-child-1-ssn", "aii_children_2_ssn"],
            ["part-a-ii-a-ii-child-1-UScheck",
                "aii_children_2_inUS | aii_children_2_notUS"],
            ["part-a-ii-a-ii-child-2-anumber", "aii_children_3_anumber"],
            ["part-a-ii-a-ii-child-2-ccob", "aii_children_3_cob"],
            ["part-a-ii-a-ii-child-2-citizenship", "aii_children_3_citizenship"],
            ["part-a-ii-a-ii-child-2-currExp", "aii_children_3_currExp"],
            ["part-a-ii-a-ii-child-2-currSts", "aii_children_3_currSts"],
            ["part-a-ii-a-ii-child-2-dob", "aii_children_3_dob"],
            ["part-a-ii-a-ii-child-2-firstName", "aii_children_3_firstName"],
            ["part-a-ii-a-ii-child-2-gender",
                "aii_children_3_male | aii_children_3_female"],
            ["part-a-ii-a-ii-child-2-i94", "aii_children_3_i94"],
            ["part-a-ii-a-ii-child-2-id", "aii_children_3_ID"],
            ["part-a-ii-a-ii-child-2-immiProc",
                "aii_children_3_inICP | aii_children_3_notICP"],
            ["part-a-ii-a-ii-child-2-inclusion",
                "aii_children_3_include | aii_children_3_notinclude"],
            ["part-a-ii-a-ii-child-2-lastEntry-date",
                "aii_children_3_lastEntry_date"],
            ["part-a-ii-a-ii-child-2-lastEntry-place",
                "aii_children_3_lastEntry_place"],
            ["part-a-ii-a-ii-child-2-lastEntry-status",
                "aii_children_3_lastEntry_sts"],
            ["part-a-ii-a-ii-child-2-lastName", "aii_children_3_lastName"],
            ["part-a-ii-a-ii-child-2-loc", "aii_children_3_loc"],
            ["part-a-ii-a-ii-child-2-maritalSts", "aii_children_3_maritalSts"],
            ["part-a-ii-a-ii-child-2-middleName", "aii_children_3_middleName"],
            ["part-a-ii-a-ii-child-2-race", "aii_children_3_race"],
            ["part-a-ii-a-ii-child-2-ssn", "aii_children_3_ssn"],
            ["part-a-ii-a-ii-child-2-UScheck",
                "aii_children_3_inUS | aii_children_3_notUS"],
            ["part-a-ii-a-ii-child-3-anumber", "aii_children_4_anumber"],
            ["part-a-ii-a-ii-child-3-ccob", "aii_children_4_cob"],
            ["part-a-ii-a-ii-child-3-citizenship", "aii_children_4_citizenship"],
            ["part-a-ii-a-ii-child-3-currExp", "aii_children_4_currExp"],
            ["part-a-ii-a-ii-child-3-currSts", "aii_children_4_currSts"],
            ["part-a-ii-a-ii-child-3-dob", "aii_children_4_dob"],
            ["part-a-ii-a-ii-child-3-firstName", "aii_children_4_firstName"],
            ["part-a-ii-a-ii-child-3-gender",
                "aii_children_4_female | aii_children_4_male"],
            ["part-a-ii-a-ii-child-3-i94", "aii_children_4_i94"],
            ["part-a-ii-a-ii-child-3-id", "aii_children_4_ID"],
            ["part-a-ii-a-ii-child-3-immiProc",
                "aii_children_4_inICP | aii_children_4_notICP"],
            ["part-a-ii-a-ii-child-3-inclusion",
                "aii_children_4_include | aii_children_4_notinclude"],
            ["part-a-ii-a-ii-child-3-lastEntry-date",
                "aii_children_4_lastEntry_date"],
            ["part-a-ii-a-ii-child-3-lastEntry-place",
                "aii_children_4_lastEntry_place"],
            ["part-a-ii-a-ii-child-3-lastEntry-status",
                "aii_children_4_lastEntry_sts"],
            ["part-a-ii-a-ii-child-3-lastName", "aii_children_4_lastName"],
            ["part-a-ii-a-ii-child-3-loc", "aii_children_4_loc"],
            ["part-a-ii-a-ii-child-3-maritalSts", "aii_children_4_maritalSts"],
            ["part-a-ii-a-ii-child-3-middleName", "aii_children_4_middleName"],
            ["part-a-ii-a-ii-child-3-race", "aii_children_4_race"],
            ["part-a-ii-a-ii-child-3-ssn", "aii_children_4_ssn"],
            ["part-a-ii-a-ii-child-3-UScheck",
                "aii_children_4_notUS | aii_children_4_inUS"],
            ["part-a-ii-a-ii-child-4-anumber", "suppA_children_1_anumber"],
            ["part-a-ii-a-ii-child-4-ccob", "suppA_children_1_cob"],
            ["part-a-ii-a-ii-child-4-citizenship", "suppA_children_1_citizenship"],
            ["part-a-ii-a-ii-child-4-currExp", "suppA_children_1_currExp"],
            ["part-a-ii-a-ii-child-4-currSts", "suppA_children_1_currSts"],
            ["part-a-ii-a-ii-child-4-dob", "suppA_children_1_dob"],
            ["part-a-ii-a-ii-child-4-firstName", "suppA_children_1_firstName"],
            ["part-a-ii-a-ii-child-4-gender",
                "suppA_children_1_male | suppA_children_1_female"],
            ["part-a-ii-a-ii-child-4-i94", "suppA_children_1_i94"],
            ["part-a-ii-a-ii-child-4-id", "suppA_children_1_ID"],
            ["part-a-ii-a-ii-child-4-immiProc",
                "suppA_children_1_notICP | suppA_children_1_ICP"],
            ["part-a-ii-a-ii-child-4-inclusion",
                "suppA_children_1_notinclude | suppA_children_1_include"],
            ["part-a-ii-a-ii-child-4-lastEntry-date",
                "suppA_children_1_lastEntry_date"],
            ["part-a-ii-a-ii-child-4-lastEntry-place",
                "suppA_children_1_lastEntry_place"],
            ["part-a-ii-a-ii-child-4-lastEntry-status",
                "suppA_children_1_lastEntry_sts"],
            ["part-a-ii-a-ii-child-4-lastName", "suppA_children_1_lastName"],
            ["part-a-ii-a-ii-child-4-loc", "suppA_children_1_loc"],
            ["part-a-ii-a-ii-child-4-maritalSts", "suppA_children_1_maritalSts"],
            ["part-a-ii-a-ii-child-4-middleName", "suppA_children_1_middleName"],
            ["part-a-ii-a-ii-child-4-race", "suppA_children_1_race"],
            ["part-a-ii-a-ii-child-4-ssn", "suppA_children_1_ssn"],
            ["part-a-ii-a-ii-child-4-UScheck",
                "suppA_children_1_inUS | suppA_children_1_notUS"],
            ["part-a-ii-a-ii-child-5-anumber", "suppA_children_2_anumber"],
            ["part-a-ii-a-ii-child-5-ccob", "suppA_children_2_cob"],
            ["part-a-ii-a-ii-child-5-citizenship", "suppA_children_2_citizenship"],
            ["part-a-ii-a-ii-child-5-currExp", "suppA_children_2_currExp"],
            ["part-a-ii-a-ii-child-5-currSts", "suppA_children_2_currSts"],
            ["part-a-ii-a-ii-child-5-dob", "suppA_children_2_dob"],
            ["part-a-ii-a-ii-child-5-firstName", "suppA_children_2_firstName"],
            ["part-a-ii-a-ii-child-5-gender",
                "suppA_children_2_male | suppA_children_2_female"],
            ["part-a-ii-a-ii-child-5-i94", "suppA_children_2_i94"],
            ["part-a-ii-a-ii-child-5-id", "suppA_children_2_ID"],
            ["part-a-ii-a-ii-child-5-immiProc",
                "suppA_children_2_notICP | suppA_children_2_ICP"],
            ["part-a-ii-a-ii-child-5-inclusion",
                "suppA_children_2_notinclude | suppA_children_2_include"],
            ["part-a-ii-a-ii-child-5-lastEntry-date",
                "suppA_children_2_lastEntry_date"],
            ["part-a-ii-a-ii-child-5-lastEntry-place",
                "suppA_children_2_lastEntry_place"],
            ["part-a-ii-a-ii-child-5-lastEntry-status",
                "suppA_children_2_lastEntry_sts"],
            ["part-a-ii-a-ii-child-5-lastName", "suppA_children_2_lastName"],
            ["part-a-ii-a-ii-child-5-loc", "suppA_children_2_loc"],
            ["part-a-ii-a-ii-child-5-maritalSts", "suppA_children_2_maritalSts"],
            ["part-a-ii-a-ii-child-5-middleName", "suppA_children_2_middleName"],
            ["part-a-ii-a-ii-child-5-race", "suppA_children_2_race"],
            ["part-a-ii-a-ii-child-5-ssn", "suppA_children_2_ssn"],
            ["part-a-ii-a-ii-child-5-UScheck",
                "suppA_children_2_inUS | suppA_children_2_notUS"],
            ["part-a-ii-a-ii-childrenNum", "aii_childrenNum"],
            ["part-a-ii-a-ii-spouse-aliases", "aii_spouseAliases"],
            ["part-a-ii-a-ii-spouse-anumber", "aii_spouseANumber"],
            ["part-a-ii-a-ii-spouse-ccob", "aii_spouseCountryBirth"],
            ["part-a-ii-a-ii-spouse-citizenship", "aii_spouseCitizenship"],
            ["part-a-ii-a-ii-spouse-currExp", "aii_spouseExpire"],
            ["part-a-ii-a-ii-spouse-currLoc", "aii_spouseLoc"],
            ["part-a-ii-a-ii-spouse-currSts", "aii_spouse_currStatus"],
            ["part-a-ii-a-ii-spouse-dob", "aii_spouseDOB"],
            ["part-a-ii-a-ii-spouse-dom", "aii_spouseDOM"],
            ["part-a-ii-a-ii-spouse-firstName", "aii_spousefirstName"],
            ["part-a-ii-a-ii-spouse-gender", "aii_spouseMale | aii_spouseFemale"],
            ["part-a-ii-a-ii-spouse-i94", "aii_spouse_i94"],
            ["part-a-ii-a-ii-spouse-id", "aii_spouseID"],
            ["part-a-ii-a-ii-spouse-inclusion",
                "aii_spouseInclude | aii_spouseNInclude"],
            ["part-a-ii-a-ii-spouse-lastEntry-date", "aii_spouseLastEntry_Date"],
            ["part-a-ii-a-ii-spouse-lastEntry-place", "aii_spouseLastEntry_place"],
            ["part-a-ii-a-ii-spouse-lastEntry-status", "aii_spouseLastEntry_status"],
            ["part-a-ii-a-ii-spouse-lastName", "aii_spouselastName"],
            ["part-a-ii-a-ii-spouse-middleName", "aii_spousemiddleName"],
            ["part-a-ii-a-ii-spouse-pom", "aii_spousePOM"],
            ["part-a-ii-a-ii-spouse-prevArrival", "aii_spouse_prevDate"],
            ["part-a-ii-a-ii-spouse-race", "aii_spouseRace"],
            ["part-a-ii-a-ii-spouse-ssn", "aii_spouseSSN"],
            ["part-a-ii-a-ii-spouse-UScheck", "aii_spouseNotUS | aii_spouseInUS"],
            ["part-a-ii-childrenCheckInp", "aii_childrenNo | aii_childrenYes"],
            ["part-a-ii-spouse-immiProc", "aii_spouseInICP | aii_spousenotICP"],
            ["part-a-ii-spouseCheck", "aii_spouse"],
            ["part-a-iii-a-iii-address-0-city", "aiii_city_1"],
            ["part-a-iii-a-iii-address-0-country", "aiii_country_1"],
            ["part-a-iii-a-iii-address-0-date-from", "aiii_from_1"],
            ["part-a-iii-a-iii-address-0-date-to", "aiii_to_1"],
            ["part-a-iii-a-iii-address-0-state", "aiii_state_1"],
            ["part-a-iii-a-iii-address-0-street", "aiii_street_1"],
            ["part-a-iii-a-iii-address-1-city", "aiii_city_2"],
            ["part-a-iii-a-iii-address-1-country", "aiii_country_2"],
            ["part-a-iii-a-iii-address-1-date-from", "aiii_from_2"],
            ["part-a-iii-a-iii-address-1-date-to", "aiii_to_2"],
            ["part-a-iii-a-iii-address-1-state", "aiii_state_2"],
            ["part-a-iii-a-iii-address-1-street", "aiii_street_2"],
            ["part-a-iii-a-iii-address-2-city", "-"],
            ["part-a-iii-a-iii-address-2-country", "-"],
            ["part-a-iii-a-iii-address-2-date-from", "-"],
            ["part-a-iii-a-iii-address-2-date-to", "-"],
            ["part-a-iii-a-iii-address-2-state", "-"],
            ["part-a-iii-a-iii-address-2-street", "-"],
            ["part-a-iii-a-iii-address-3-city", "-"],
            ["part-a-iii-a-iii-address-3-country", "-"],
            ["part-a-iii-a-iii-address-3-date-from", "-"],
            ["part-a-iii-a-iii-address-3-date-to", "-"],
            ["part-a-iii-a-iii-address-3-state", "-"],
            ["part-a-iii-a-iii-address-3-street", "-"],
            ["part-a-iii-a-iii-address-4-city", "-"],
            ["part-a-iii-a-iii-address-4-country", "-"],
            ["part-a-iii-a-iii-address-4-date-from", "-"],
            ["part-a-iii-a-iii-address-4-date-to", "-"],
            ["part-a-iii-a-iii-address-4-state", "-"],
            ["part-a-iii-a-iii-address-4-street", "-"],
            ["part-a-iii-a-iii-address-5-city", "-"],
            ["part-a-iii-a-iii-address-5-country", "-"],
            ["part-a-iii-a-iii-address-5-date-from", "-"],
            ["part-a-iii-a-iii-address-5-date-to", "-"],
            ["part-a-iii-a-iii-address-5-state", "-"],
            ["part-a-iii-a-iii-address-5-street", "-"],
            ["part-a-iii-a-iii-education-0-dates-from", "aiii_school_from_1"],
            ["part-a-iii-a-iii-education-0-dates-to", "aiii_school_to_1"],
            ["part-a-iii-a-iii-education-0-loc", "aiii_school_add_1"],
            ["part-a-iii-a-iii-education-0-name", "aiii_school_name_1"],
            ["part-a-iii-a-iii-education-0-type", "aiii_school_type_1"],
            ["part-a-iii-a-iii-education-1-dates-from", "aiii_school_from_2"],
            ["part-a-iii-a-iii-education-1-dates-to", "aiii_school_to_2"],
            ["part-a-iii-a-iii-education-1-loc", "aiii_school_add_2"],
            ["part-a-iii-a-iii-education-1-name", "aiii_school_name_2"],
            ["part-a-iii-a-iii-education-1-type", "aiii_school_type_2"],
            ["part-a-iii-a-iii-education-2-dates-from", "aiii_school_from_3"],
            ["part-a-iii-a-iii-education-2-dates-to", "aiii_school_to_3"],
            ["part-a-iii-a-iii-education-2-loc", "aiii_school_add_3"],
            ["part-a-iii-a-iii-education-2-name", "aiii_school_name_3"],
            ["part-a-iii-a-iii-education-2-type", "aiii_school_type_3"],
            ["part-a-iii-a-iii-education-3-dates-from", "aiii_school_from_4"],
            ["part-a-iii-a-iii-education-3-dates-to", "aiii_school_to_4"],
            ["part-a-iii-a-iii-education-3-loc", "aiii_school_add_4"],
            ["part-a-iii-a-iii-education-3-name", "aiii_school_name_4"],
            ["part-a-iii-a-iii-education-3-type", "aiii_school_type_4"],
            ["part-a-iii-a-iii-education-4-dates-from", "-"],
            ["part-a-iii-a-iii-education-4-dates-to", "-"],
            ["part-a-iii-a-iii-education-4-loc", "-"],
            ["part-a-iii-a-iii-education-4-name", "-"],
            ["part-a-iii-a-iii-education-4-type", "-"],
            ["part-a-iii-a-iii-education-5-dates-from", "-"],
            ["part-a-iii-a-iii-education-5-dates-to", "-"],
            ["part-a-iii-a-iii-education-5-loc", "-"],
            ["part-a-iii-a-iii-education-5-name", "-"],
            ["part-a-iii-a-iii-education-5-type", "-"],
            ["part-a-iii-a-iii-employment-0-address", "aiii_empl_add_1"],
            ["part-a-iii-a-iii-employment-0-dates-from", "aiii_empl_from_1"],
            ["part-a-iii-a-iii-employment-0-dates-to", "aiii_empl_to_1"],
            ["part-a-iii-a-iii-employment-0-name", "aiii_empl_add_1"],
            ["part-a-iii-a-iii-employment-0-occ", "aiii_empl_occ_1"],
            ["part-a-iii-a-iii-employment-1-address", "aiii_empl_add_2"],
            ["part-a-iii-a-iii-employment-1-dates-from", "aiii_empl_from_2"],
            ["part-a-iii-a-iii-employment-1-dates-to", "aiii_empl_to_2"],
            ["part-a-iii-a-iii-employment-1-name", "aiii_empl_add_2"],
            ["part-a-iii-a-iii-employment-1-occ", "aiii_empl_occ_2"],
            ["part-a-iii-a-iii-employment-2-address", "aiii_empl_add_3"],
            ["part-a-iii-a-iii-employment-2-dates-from", "aiii_empl_from_3"],
            ["part-a-iii-a-iii-employment-2-dates-to", "aiii_empl_to_3"],
            ["part-a-iii-a-iii-employment-2-name", "aiii_empl_add_3"],
            ["part-a-iii-a-iii-employment-2-occ", "aiii_empl_occ_3"],
            ["part-a-iii-a-iii-employment-3-address", "-"],
            ["part-a-iii-a-iii-employment-3-dates-from", "-"],
            ["part-a-iii-a-iii-employment-3-dates-to", "-"],
            ["part-a-iii-a-iii-employment-3-name", "-"],
            ["part-a-iii-a-iii-employment-3-occ", "-"],
            ["part-a-iii-a-iii-employment-4-address", "-"],
            ["part-a-iii-a-iii-employment-4-dates-from", "-"],
            ["part-a-iii-a-iii-employment-4-dates-to", "-"],
            ["part-a-iii-a-iii-employment-4-name", "-"],
            ["part-a-iii-a-iii-employment-4-occ", "-"],
            ["part-a-iii-a-iii-father-ccob", "aiii_father_ccob"],
            ["part-a-iii-a-iii-father-loc", "aiii_father_currLoc"],
            ["part-a-iii-a-iii-father-name", "aiii_father_name"],
            ["part-a-iii-a-iii-mother-ccob", "aiii_mother_ccob"],
            ["part-a-iii-a-iii-mother-loc", "aiii_mother_currLoc"],
            ["part-a-iii-a-iii-mother-name", "aiii_mother_name"],
            ["part-a-iii-a-iii-residence-0-city", "aiii_all_city_1"],
            ["part-a-iii-a-iii-residence-0-country", "aiii_all_country_1"],
            ["part-a-iii-a-iii-residence-0-date-from", "aiii_all_from_1"],
            ["part-a-iii-a-iii-residence-0-date-to", "aiii_all_to_1"],
            ["part-a-iii-a-iii-residence-0-state", "aiii_all_state_1"],
            ["part-a-iii-a-iii-residence-0-street", "aiii_all_place_1"],
            ["part-a-iii-a-iii-residence-1-city", "aiii_all_city_2"],
            ["part-a-iii-a-iii-residence-1-country", "aiii_all_country_2"],
            ["part-a-iii-a-iii-residence-1-date-from", "aiii_all_from_2"],
            ["part-a-iii-a-iii-residence-1-date-to", "aiii_all_to_2"],
            ["part-a-iii-a-iii-residence-1-state", "aiii_all_state_2"],
            ["part-a-iii-a-iii-residence-1-street", "aiii_all_place_2"],
            ["part-a-iii-a-iii-residence-2-city", "aiii_all_city_3"],
            ["part-a-iii-a-iii-residence-2-country", "aiii_all_country_3"],
            ["part-a-iii-a-iii-residence-2-date-from", "aiii_all_from_3"],
            ["part-a-iii-a-iii-residence-2-date-to", "aiii_all_to_3"],
            ["part-a-iii-a-iii-residence-2-state", "aiii_all_state_3"],
            ["part-a-iii-a-iii-residence-2-street", "aiii_all_place_3"],
            ["part-a-iii-a-iii-residence-3-city", "aiii_all_city_4"],
            ["part-a-iii-a-iii-residence-3-country", "aiii_all_country_4"],
            ["part-a-iii-a-iii-residence-3-date-from", "aiii_all_from_4"],
            ["part-a-iii-a-iii-residence-3-date-to", "aiii_all_to_4"],
            ["part-a-iii-a-iii-residence-3-state", "aiii_all_state_4"],
            ["part-a-iii-a-iii-residence-3-street", "aiii_all_place_4"],
            ["part-a-iii-a-iii-residence-4-city", "aiii_all_city_5"],
            ["part-a-iii-a-iii-residence-4-country", "aiii_all_country_5"],
            ["part-a-iii-a-iii-residence-4-date-from", "aiii_all_from_5"],
            ["part-a-iii-a-iii-residence-4-date-to", "aiii_all_to_5"],
            ["part-a-iii-a-iii-residence-4-state", "aiii_all_state_5"],
            ["part-a-iii-a-iii-residence-4-street", "aiii_all_place_5"],
            ["part-a-iii-a-iii-residence-5-city", "-"],
            ["part-a-iii-a-iii-residence-5-country", "-"],
            ["part-a-iii-a-iii-residence-5-date-from", "-"],
            ["part-a-iii-a-iii-residence-5-date-to", "-"],
            ["part-a-iii-a-iii-residence-5-state", "-"],
            ["part-a-iii-a-iii-residence-5-street", "-"],
            ["part-a-iii-a-iii-residence-6-city", "-"],
            ["part-a-iii-a-iii-residence-6-country", "-"],
            ["part-a-iii-a-iii-residence-6-date-from", "-"],
            ["part-a-iii-a-iii-residence-6-date-to", "-"],
            ["part-a-iii-a-iii-residence-6-state", "-"],
            ["part-a-iii-a-iii-residence-6-street", "-"],
            ["part-a-iii-a-iii-residence-7-city", "-"],
            ["part-a-iii-a-iii-residence-7-country", "-"],
            ["part-a-iii-a-iii-residence-7-date-from", "-"],
            ["part-a-iii-a-iii-residence-7-date-to", "-"],
            ["part-a-iii-a-iii-residence-7-state", "-"],
            ["part-a-iii-a-iii-residence-7-street", "-"],
            ["part-a-iii-a-iii-residence-8-city", "-"],
            ["part-a-iii-a-iii-residence-8-country", "-"],
            ["part-a-iii-a-iii-residence-8-date-from", "-"],
            ["part-a-iii-a-iii-residence-8-date-to", "-"],
            ["part-a-iii-a-iii-residence-8-state", "-"],
            ["part-a-iii-a-iii-residence-8-street", "-"],
            ["part-a-iii-a-iii-sibling-0-ccob", "aiii_sibling_ccob_1"],
            ["part-a-iii-a-iii-sibling-0-loc", "aiii_sibling_currLoc_1"],
            ["part-a-iii-a-iii-sibling-0-name", "aiii_sibling_name_1"],
            ["part-a-iii-a-iii-sibling-1-ccob", "aiii_sibling_ccob_2"],
            ["part-a-iii-a-iii-sibling-1-loc", "aiii_sibling_currLoc_2"],
            ["part-a-iii-a-iii-sibling-1-name", "aiii_sibling_name_2"],
            ["part-a-iii-a-iii-sibling-2-ccob", "aiii_sibling_ccob_3"],
            ["part-a-iii-a-iii-sibling-2-loc", "aiii_sibling_currLoc_3"],
            ["part-a-iii-a-iii-sibling-2-name", "aiii_sibling_name_3"],
            ["part-a-iii-a-iii-sibling-3-ccob", "aiii_sibling_ccob_4"],
            ["part-a-iii-a-iii-sibling-3-loc", "aiii_sibling_currLoc_4"],
            ["part-a-iii-a-iii-sibling-3-name", "aiii_sibling_name_4"],
            ["part-a-iii-a-iii-sibling-4-ccob", "-"],
            ["part-a-iii-a-iii-sibling-4-loc", "-"],
            ["part-a-iii-a-iii-sibling-4-name", "-"],
            ["part-a-iii-father-dec", "aiii_father_dec"],
            ["part-a-iii-mother-dec", "aiii_mother_dec"],
            ["part-a-iii-sibling-0-dec", "aiii_sibling_dec_1"],
            ["part-a-iii-sibling-1-dec", "aiii_sibling_dec_2"],
            ["part-a-iii-sibling-2-dec", "aiii_sibling_dec_3"],
            ["part-a-iii-sibling-3-dec", "aiii_sibling_dec_4"],
            ["part-a-iii-sibling-4-dec", "-"],
            ["part-b-b-crimeCheck", "b_accuseYes | b_accuseNo"],
            ["part-b-b-crimeResp", "b_accuseReason"],
            ["part-b-b-fearCheck", "b_fearHarm_no | b_fearHarm_yes"],
            ["part-b-b-fear-what", "b_fearHarm_reason"],
            ["part-b-b-fear-who", "b_fearHarm_reason"],
            ["part-b-b-fear-why", "b_fearHarm_reason"],
            ["part-b-b-harmCheck", "b_harmNo | b_harmYes"],
            ["part-b-b-harm-what", "b_harmReason"],
            ["part-b-b-harm-when", "b_harmReason"],
            ["part-b-b-harm-who", "b_harmReason"],
            ["part-b-b-harm-why", "b_harmReason"],
            ["part-b-b-orgAssCheck", "b_orgYes | b_orgNo"],
            ["part-b-b-orgAssResp", "b_orgDets"],
            ["part-b-b-orgPartCheck", "b_orgBel_no | b_orgBel_yes"],
            ["part-b-b-orgPartResp", "b_orgBel_dets"],
            ["part-b-b-orgTortureCheck", "b_tortureNo | b_tortureYes"],
            ["part-b-b-orgTortureResp", "b_torture_dets"],
            ["part-b-reason", "b_membership | b_nationality | b_race | b_religion | b_torture | b_opinion"],
            ["part-c-c-causedHarm", "c_prevViol_dets"],
            ["part-c-c-causedHarmCheck", "c_prevViol_no | c_prevViol_yes"],
            ["part-c-c-crimeComm", "c_crime_dets"],
            ["part-c-c-crimeCommCheck", "c_crime_no | c_crime_yes"],
            ["part-c-c-inCountry", "c_prevCountry_no | c_prevCountry_yes"],
            ["part-c-c-lawfulStatusCheck",
                "c_prevCountryAppl_no | c_prevCountryAppl_yes"],
            ["part-c-c-lawfulStatusExp", "c_prevCountryAppl_dets"],
            ["part-c-c-leftCountry", "c_retCountry_dets"],
            ["part-c-c-leftCountryCheck", "c_retCountry_no | c_retCountry_yes"],
            ["part-c-c-oneYear", "c_more1_reason"],
            ["part-c-c-oneYearCheck", "c_more1_no | c_more1_yes"],
            ["part-c-c-prevAppl", "c_applPrev_decision"],
            ["part-c-c-prevApplCheck", "c_applPrev_no | c_applPrev_yes"],
            ["part-d-d-additionalApplnCheck",
                "d_otherAssist_no | d_otherAssist_yes"],
            ["part-d-d-assistanceCheck", "d_famAssist_no | d_famAssist_yes"],
            ["part-d-d-assistName-0", "d_famAssist_name_1"],
            ["part-d-d-assistName-1", "d_famAssist_name_2"],
            ["part-d-d-assistName-2", "-"],
            ["part-d-d-assistName-3", "-"],
            ["part-d-d-assistName-4", "-"],
            ["part-d-d-completeName", "d_fullName"],
            ["part-d-d-nativeName", "d_nativeName"],
            ["part-d-d-relationship-0", "d_famAssist_rel_1"],
            ["part-d-d-relationship-1", "d_famAssist_rel_2"],
            ["part-d-d-relationship-2", "-"],
            ["part-d-d-relationship-3", "-"],
            ["part-d-d-relationship-4", "-"],
            ["part-d-d-reprCheck", "d_counselAssist_no | d_counselAssist_yes"],
            ["part-d-d-sign-date", "d_date"],
            ["part-suppAB-suppAB-name", "suppA_name | suppB_name"],
            ["part-suppAB-suppAB-part-0", "suppB_part"],
            ["part-d-hiddenFileInput", "suppA_sign"],
            ["part-d-hiddenFileInput", "suppB_sign"],
            ["part-suppAB-suppAB-anumber", "suppA_anum | suppB_anumber"],
            ["part-d-hiddenFileInput", "d_sign"],
            ["part-suppAB-suppAB-date", "suppA_date | suppB_date"],
            ["part-suppAB-suppAB-part-1", "-"],
            ["part-suppAB-suppAB-ques-0", "suppB_ques"],
            ["part-suppAB-suppAB-ques-1", "-"],
            ["part-suppAB-suppAB-resp-0", "suppB_dets"],
            ["part-suppAB-suppAB-resp-1", "-"],
            ["part-a-i-a-i-telArea", "ai_areaCode"],            
            ["part-a-i-a-i-mailTelArea", "ai_MailareaCode"],
        ]

        self.web_form_data = {
            0: ["part-a-i-a-i-aliases", ""],
            1: ["part-a-i-a-i-anumber", ""],
            2: ["part-a-i-a-i-apt", ""],
            3: ["part-a-i-a-i-ccob", ""],
            4: ["part-a-i-a-i-citizenship", ""],
            5: ["part-a-i-a-i-city", ""],
            6: ["part-a-i-a-i-currDate", ""],
            7: ["part-a-i-a-i-currExp", ""],
            8: ["part-a-i-a-i-currPlace", ""],
            9: ["part-a-i-a-i-currSts", ""],
            10: ["part-a-i-a-i-date-0", ""],
            11: ["part-a-i-a-i-date-1", ""],
            12: ["part-a-i-a-i-date-2", ""],
            13: ["part-a-i-a-i-date-3", ""],
            14: ["part-a-i-a-i-date-4", ""],
            15: ["part-a-i-a-i-date-5", ""],
            16: ["part-a-i-a-i-dob", ""],
            17: ["part-a-i-a-i-expDate", ""],
            18: ["part-a-i-a-i-firstName", ""],
            19: ["part-a-i-a-i-gender", ""],
            20: ["part-a-i-a-i-i94", ""],
            21: ["part-a-i-a-i-immiProceedings", ""],
            22: ["part-a-i-a-i-lastName", ""],
            23: ["part-a-i-a-i-leftDate", ""],
            24: ["part-a-i-a-i-mailApt", ""],
            25: ["part-a-i-a-i-mailCity", ""],
            26: ["part-a-i-a-i-mailCO", ""],
            27: ["part-a-i-a-i-mailState", ""],
            28: ["part-a-i-a-i-mailStreet", ""],
            29: ["part-a-i-a-i-mailTel", ""],
            30: ["part-a-i-a-i-mailZipCode", ""],
            31: ["part-a-i-a-i-maritalSts", ""],
            32: ["part-a-i-a-i-middleName", ""],
            33: ["part-a-i-a-i-nationality", ""],
            34: ["part-a-i-a-i-nativeLang", ""],
            35: ["part-a-i-a-i-otherFluency", ""],
            36: ["part-a-i-a-i-passportInfo", ""],
            37: ["part-a-i-a-i-passportNum", ""],
            38: ["part-a-i-a-i-place-0", ""],
            39: ["part-a-i-a-i-place-1", ""],
            40: ["part-a-i-a-i-place-2", ""],
            41: ["part-a-i-a-i-place-3", ""],
            42: ["part-a-i-a-i-place-4", ""],
            43: ["part-a-i-a-i-place-5", ""],
            44: ["part-a-i-a-i-race", ""],
            45: ["part-a-i-a-i-religion", ""],
            46: ["part-a-i-a-i-ssn", ""],
            47: ["part-a-i-a-i-state", ""],
            48: ["part-a-i-a-i-status-0", ""],
            49: ["part-a-i-a-i-status-1", ""],
            50: ["part-a-i-a-i-status-2", ""],
            51: ["part-a-i-a-i-status-3", ""],
            52: ["part-a-i-a-i-status-4", ""],
            53: ["part-a-i-a-i-status-5", ""],
            54: ["part-a-i-a-i-street", ""],
            55: ["part-a-i-a-i-tel", ""],
            56: ["part-a-i-a-i-traveDocNum", ""],
            57: ["part-a-i-a-i-uscis", ""],
            58: ["part-a-i-a-i-zipCode", ""],
            59: ["part-a-i-eng_fluency", ""],
            60: ["part-a-ii-a-ii-child-0-anumber", ""],
            61: ["part-a-ii-a-ii-child-0-ccob", ""],
            62: ["part-a-ii-a-ii-child-0-citizenship", ""],
            63: ["part-a-ii-a-ii-child-0-currExp", ""],
            64: ["part-a-ii-a-ii-child-0-currSts", ""],
            65: ["part-a-ii-a-ii-child-0-dob", ""],
            66: ["part-a-ii-a-ii-child-0-firstName", ""],
            67: ["part-a-ii-a-ii-child-0-gender", ""],
            68: ["part-a-ii-a-ii-child-0-i94", ""],
            69: ["part-a-ii-a-ii-child-0-id", ""],
            70: ["part-a-ii-a-ii-child-0-immiProc", ""],
            71: ["part-a-ii-a-ii-child-0-inclusion", ""],
            72: ["part-a-ii-a-ii-child-0-lastEntry-date", ""],
            73: ["part-a-ii-a-ii-child-0-lastEntry-place", ""],
            74: ["part-a-ii-a-ii-child-0-lastEntry-status", ""],
            75: ["part-a-ii-a-ii-child-0-lastName", ""],
            76: ["part-a-ii-a-ii-child-0-loc", ""],
            77: ["part-a-ii-a-ii-child-0-maritalSts", ""],
            78: ["part-a-ii-a-ii-child-0-middleName", ""],
            79: ["part-a-ii-a-ii-child-0-race", ""],
            80: ["part-a-ii-a-ii-child-0-ssn", ""],
            81: ["part-a-ii-a-ii-child-0-UScheck", ""],
            82: ["part-a-ii-a-ii-child-1-anumber", ""],
            83: ["part-a-ii-a-ii-child-1-ccob", ""],
            84: ["part-a-ii-a-ii-child-1-citizenship", ""],
            85: ["part-a-ii-a-ii-child-1-currExp", ""],
            86: ["part-a-ii-a-ii-child-1-currSts", ""],
            87: ["part-a-ii-a-ii-child-1-dob", ""],
            88: ["part-a-ii-a-ii-child-1-firstName", ""],
            89: ["part-a-ii-a-ii-child-1-gender", ""],
            90: ["part-a-ii-a-ii-child-1-i94", ""],
            91: ["part-a-ii-a-ii-child-1-id", ""],
            92: ["part-a-ii-a-ii-child-1-immiProc", ""],
            93: ["part-a-ii-a-ii-child-1-inclusion", ""],
            94: ["part-a-ii-a-ii-child-1-lastEntry-date", ""],
            95: ["part-a-ii-a-ii-child-1-lastEntry-place", ""],
            96: ["part-a-ii-a-ii-child-1-lastEntry-status", ""],
            97: ["part-a-ii-a-ii-child-1-lastName", ""],
            98: ["part-a-ii-a-ii-child-1-loc", ""],
            99: ["part-a-ii-a-ii-child-1-maritalSts", ""],
            100: ["part-a-ii-a-ii-child-1-middleName", ""],
            101: ["part-a-ii-a-ii-child-1-race", ""],
            102: ["part-a-ii-a-ii-child-1-ssn", ""],
            103: ["part-a-ii-a-ii-child-1-UScheck", ""],
            104: ["part-a-ii-a-ii-child-2-anumber", ""],
            105: ["part-a-ii-a-ii-child-2-ccob", ""],
            106: ["part-a-ii-a-ii-child-2-citizenship", ""],
            107: ["part-a-ii-a-ii-child-2-currExp", ""],
            108: ["part-a-ii-a-ii-child-2-currSts", ""],
            109: ["part-a-ii-a-ii-child-2-dob", ""],
            110: ["part-a-ii-a-ii-child-2-firstName", ""],
            111: ["part-a-ii-a-ii-child-2-gender", ""],
            112: ["part-a-ii-a-ii-child-2-i94", ""],
            113: ["part-a-ii-a-ii-child-2-id", ""],
            114: ["part-a-ii-a-ii-child-2-immiProc", ""],
            115: ["part-a-ii-a-ii-child-2-inclusion", ""],
            116: ["part-a-ii-a-ii-child-2-lastEntry-date", ""],
            117: ["part-a-ii-a-ii-child-2-lastEntry-place", ""],
            118: ["part-a-ii-a-ii-child-2-lastEntry-status", ""],
            119: ["part-a-ii-a-ii-child-2-lastName", ""],
            120: ["part-a-ii-a-ii-child-2-loc", ""],
            121: ["part-a-ii-a-ii-child-2-maritalSts", ""],
            122: ["part-a-ii-a-ii-child-2-middleName", ""],
            123: ["part-a-ii-a-ii-child-2-race", ""],
            124: ["part-a-ii-a-ii-child-2-ssn", ""],
            125: ["part-a-ii-a-ii-child-2-UScheck", ""],
            126: ["part-a-ii-a-ii-child-3-anumber", ""],
            127: ["part-a-ii-a-ii-child-3-ccob", ""],
            128: ["part-a-ii-a-ii-child-3-citizenship", ""],
            129: ["part-a-ii-a-ii-child-3-currExp", ""],
            130: ["part-a-ii-a-ii-child-3-currSts", ""],
            131: ["part-a-ii-a-ii-child-3-dob", ""],
            132: ["part-a-ii-a-ii-child-3-firstName", ""],
            133: ["part-a-ii-a-ii-child-3-gender", ""],
            134: ["part-a-ii-a-ii-child-3-i94", ""],
            135: ["part-a-ii-a-ii-child-3-id", ""],
            136: ["part-a-ii-a-ii-child-3-immiProc", ""],
            137: ["part-a-ii-a-ii-child-3-inclusion", ""],
            138: ["part-a-ii-a-ii-child-3-lastEntry-date", ""],
            139: ["part-a-ii-a-ii-child-3-lastEntry-place", ""],
            140: ["part-a-ii-a-ii-child-3-lastEntry-status", ""],
            141: ["part-a-ii-a-ii-child-3-lastName", ""],
            142: ["part-a-ii-a-ii-child-3-loc", ""],
            143: ["part-a-ii-a-ii-child-3-maritalSts", ""],
            144: ["part-a-ii-a-ii-child-3-middleName", ""],
            145: ["part-a-ii-a-ii-child-3-race", ""],
            146: ["part-a-ii-a-ii-child-3-ssn", ""],
            147: ["part-a-ii-a-ii-child-3-UScheck", ""],
            148: ["part-a-ii-a-ii-child-4-anumber", ""],
            149: ["part-a-ii-a-ii-child-4-ccob", ""],
            150: ["part-a-ii-a-ii-child-4-citizenship", ""],
            151: ["part-a-ii-a-ii-child-4-currExp", ""],
            152: ["part-a-ii-a-ii-child-4-currSts", ""],
            153: ["part-a-ii-a-ii-child-4-dob", ""],
            154: ["part-a-ii-a-ii-child-4-firstName", ""],
            155: ["part-a-ii-a-ii-child-4-gender", ""],
            156: ["part-a-ii-a-ii-child-4-i94", ""],
            157: ["part-a-ii-a-ii-child-4-id", ""],
            158: ["part-a-ii-a-ii-child-4-immiProc", ""],
            159: ["part-a-ii-a-ii-child-4-inclusion", ""],
            160: ["part-a-ii-a-ii-child-4-lastEntry-date", ""],
            161: ["part-a-ii-a-ii-child-4-lastEntry-place", ""],
            162: ["part-a-ii-a-ii-child-4-lastEntry-status", ""],
            163: ["part-a-ii-a-ii-child-4-lastName", ""],
            164: ["part-a-ii-a-ii-child-4-loc", ""],
            165: ["part-a-ii-a-ii-child-4-maritalSts", ""],
            166: ["part-a-ii-a-ii-child-4-middleName", ""],
            167: ["part-a-ii-a-ii-child-4-race", ""],
            168: ["part-a-ii-a-ii-child-4-ssn", ""],
            169: ["part-a-ii-a-ii-child-4-UScheck", ""],
            170: ["part-a-ii-a-ii-child-5-anumber", ""],
            171: ["part-a-ii-a-ii-child-5-ccob", ""],
            172: ["part-a-ii-a-ii-child-5-citizenship", ""],
            173: ["part-a-ii-a-ii-child-5-currExp", ""],
            174: ["part-a-ii-a-ii-child-5-currSts", ""],
            175: ["part-a-ii-a-ii-child-5-dob", ""],
            176: ["part-a-ii-a-ii-child-5-firstName", ""],
            177: ["part-a-ii-a-ii-child-5-gender", ""],
            178: ["part-a-ii-a-ii-child-5-i94", ""],
            179: ["part-a-ii-a-ii-child-5-id", ""],
            180: ["part-a-ii-a-ii-child-5-immiProc", ""],
            181: ["part-a-ii-a-ii-child-5-inclusion", ""],
            182: ["part-a-ii-a-ii-child-5-lastEntry-date", ""],
            183: ["part-a-ii-a-ii-child-5-lastEntry-place", ""],
            184: ["part-a-ii-a-ii-child-5-lastEntry-status", ""],
            185: ["part-a-ii-a-ii-child-5-lastName", ""],
            186: ["part-a-ii-a-ii-child-5-loc", ""],
            187: ["part-a-ii-a-ii-child-5-maritalSts", ""],
            188: ["part-a-ii-a-ii-child-5-middleName", ""],
            189: ["part-a-ii-a-ii-child-5-race", ""],
            190: ["part-a-ii-a-ii-child-5-ssn", ""],
            191: ["part-a-ii-a-ii-child-5-UScheck", ""],
            192: ["part-a-ii-a-ii-childrenNum", ""],
            193: ["part-a-ii-a-ii-spouse-aliases", ""],
            194: ["part-a-ii-a-ii-spouse-anumber", ""],
            195: ["part-a-ii-a-ii-spouse-ccob", ""],
            196: ["part-a-ii-a-ii-spouse-citizenship", ""],
            197: ["part-a-ii-a-ii-spouse-currExp", ""],
            198: ["part-a-ii-a-ii-spouse-currLoc", ""],
            199: ["part-a-ii-a-ii-spouse-currSts", ""],
            200: ["part-a-ii-a-ii-spouse-dob", ""],
            201: ["part-a-ii-a-ii-spouse-dom", ""],
            202: ["part-a-ii-a-ii-spouse-firstName", ""],
            203: ["part-a-ii-a-ii-spouse-gender", ""],
            204: ["part-a-ii-a-ii-spouse-i94", ""],
            205: ["part-a-ii-a-ii-spouse-id", ""],
            206: ["part-a-ii-a-ii-spouse-inclusion", ""],
            207: ["part-a-ii-a-ii-spouse-lastEntry-date", ""],
            208: ["part-a-ii-a-ii-spouse-lastEntry-place", ""],
            209: ["part-a-ii-a-ii-spouse-lastEntry-status", ""],
            210: ["part-a-ii-a-ii-spouse-lastName", ""],
            211: ["part-a-ii-a-ii-spouse-middleName", ""],
            212: ["part-a-ii-a-ii-spouse-pom", ""],
            213: ["part-a-ii-a-ii-spouse-prevArrival", ""],
            214: ["part-a-ii-a-ii-spouse-race", ""],
            215: ["part-a-ii-a-ii-spouse-ssn", ""],
            216: ["part-a-ii-a-ii-spouse-UScheck", ""],
            217: ["part-a-ii-childrenCheckInp", ""],
            218: ["part-a-ii-spouse-immiProc", ""],
            219: ["part-a-ii-spouseCheck", ""],
            220: ["part-a-iii-a-iii-address-0-city", ""],
            221: ["part-a-iii-a-iii-address-0-country", ""],
            222: ["part-a-iii-a-iii-address-0-date-from", ""],
            223: ["part-a-iii-a-iii-address-0-date-to", ""],
            224: ["part-a-iii-a-iii-address-0-state", ""],
            225: ["part-a-iii-a-iii-address-0-street", ""],
            226: ["part-a-iii-a-iii-address-1-city", ""],
            227: ["part-a-iii-a-iii-address-1-country", ""],
            228: ["part-a-iii-a-iii-address-1-date-from", ""],
            229: ["part-a-iii-a-iii-address-1-date-to", ""],
            230: ["part-a-iii-a-iii-address-1-state", ""],
            231: ["part-a-iii-a-iii-address-1-street", ""],
            232: ["part-a-iii-a-iii-address-2-city", ""],
            233: ["part-a-iii-a-iii-address-2-country", ""],
            234: ["part-a-iii-a-iii-address-2-date-from", ""],
            235: ["part-a-iii-a-iii-address-2-date-to", ""],
            236: ["part-a-iii-a-iii-address-2-state", ""],
            237: ["part-a-iii-a-iii-address-2-street", ""],
            238: ["part-a-iii-a-iii-address-3-city", ""],
            239: ["part-a-iii-a-iii-address-3-country", ""],
            240: ["part-a-iii-a-iii-address-3-date-from", ""],
            241: ["part-a-iii-a-iii-address-3-date-to", ""],
            242: ["part-a-iii-a-iii-address-3-state", ""],
            243: ["part-a-iii-a-iii-address-3-street", ""],
            244: ["part-a-iii-a-iii-address-4-city", ""],
            245: ["part-a-iii-a-iii-address-4-country", ""],
            246: ["part-a-iii-a-iii-address-4-date-from", ""],
            247: ["part-a-iii-a-iii-address-4-date-to", ""],
            248: ["part-a-iii-a-iii-address-4-state", ""],
            249: ["part-a-iii-a-iii-address-4-street", ""],
            250: ["part-a-iii-a-iii-address-5-city", ""],
            251: ["part-a-iii-a-iii-address-5-country", ""],
            252: ["part-a-iii-a-iii-address-5-date-from", ""],
            253: ["part-a-iii-a-iii-address-5-date-to", ""],
            254: ["part-a-iii-a-iii-address-5-state", ""],
            255: ["part-a-iii-a-iii-address-5-street", ""],
            256: ["part-a-iii-a-iii-education-0-dates-from", ""],
            257: ["part-a-iii-a-iii-education-0-dates-to", ""],
            258: ["part-a-iii-a-iii-education-0-loc", ""],
            259: ["part-a-iii-a-iii-education-0-name", ""],
            260: ["part-a-iii-a-iii-education-0-type", ""],
            261: ["part-a-iii-a-iii-education-1-dates-from", ""],
            262: ["part-a-iii-a-iii-education-1-dates-to", ""],
            263: ["part-a-iii-a-iii-education-1-loc", ""],
            264: ["part-a-iii-a-iii-education-1-name", ""],
            265: ["part-a-iii-a-iii-education-1-type", ""],
            266: ["part-a-iii-a-iii-education-2-dates-from", ""],
            267: ["part-a-iii-a-iii-education-2-dates-to", ""],
            268: ["part-a-iii-a-iii-education-2-loc", ""],
            269: ["part-a-iii-a-iii-education-2-name", ""],
            270: ["part-a-iii-a-iii-education-2-type", ""],
            271: ["part-a-iii-a-iii-education-3-dates-from", ""],
            272: ["part-a-iii-a-iii-education-3-dates-to", ""],
            273: ["part-a-iii-a-iii-education-3-loc", ""],
            274: ["part-a-iii-a-iii-education-3-name", ""],
            275: ["part-a-iii-a-iii-education-3-type", ""],
            276: ["part-a-iii-a-iii-education-4-dates-from", ""],
            277: ["part-a-iii-a-iii-education-4-dates-to", ""],
            278: ["part-a-iii-a-iii-education-4-loc", ""],
            279: ["part-a-iii-a-iii-education-4-name", ""],
            280: ["part-a-iii-a-iii-education-4-type", ""],
            281: ["part-a-iii-a-iii-education-5-dates-from", ""],
            282: ["part-a-iii-a-iii-education-5-dates-to", ""],
            283: ["part-a-iii-a-iii-education-5-loc", ""],
            284: ["part-a-iii-a-iii-education-5-name", ""],
            285: ["part-a-iii-a-iii-education-5-type", ""],
            286: ["part-a-iii-a-iii-employment-0-address", ""],
            287: ["part-a-iii-a-iii-employment-0-dates-from", ""],
            288: ["part-a-iii-a-iii-employment-0-dates-to", ""],
            289: ["part-a-iii-a-iii-employment-0-name", ""],
            290: ["part-a-iii-a-iii-employment-0-occ", ""],
            291: ["part-a-iii-a-iii-employment-1-address", ""],
            292: ["part-a-iii-a-iii-employment-1-dates-from", ""],
            293: ["part-a-iii-a-iii-employment-1-dates-to", ""],
            294: ["part-a-iii-a-iii-employment-1-name", ""],
            295: ["part-a-iii-a-iii-employment-1-occ", ""],
            296: ["part-a-iii-a-iii-employment-2-address", ""],
            297: ["part-a-iii-a-iii-employment-2-dates-from", ""],
            298: ["part-a-iii-a-iii-employment-2-dates-to", ""],
            299: ["part-a-iii-a-iii-employment-2-name", ""],
            300: ["part-a-iii-a-iii-employment-2-occ", ""],
            301: ["part-a-iii-a-iii-employment-3-address", ""],
            302: ["part-a-iii-a-iii-employment-3-dates-from", ""],
            303: ["part-a-iii-a-iii-employment-3-dates-to", ""],
            304: ["part-a-iii-a-iii-employment-3-name", ""],
            305: ["part-a-iii-a-iii-employment-3-occ", ""],
            306: ["part-a-iii-a-iii-employment-4-address", ""],
            307: ["part-a-iii-a-iii-employment-4-dates-from", ""],
            308: ["part-a-iii-a-iii-employment-4-dates-to", ""],
            309: ["part-a-iii-a-iii-employment-4-name", ""],
            310: ["part-a-iii-a-iii-employment-4-occ", ""],
            311: ["part-a-iii-a-iii-father-ccob", ""],
            312: ["part-a-iii-a-iii-father-loc", ""],
            313: ["part-a-iii-a-iii-father-name", ""],
            314: ["part-a-iii-a-iii-mother-ccob", ""],
            315: ["part-a-iii-a-iii-mother-loc", ""],
            316: ["part-a-iii-a-iii-mother-name", ""],
            317: ["part-a-iii-a-iii-residence-0-city", ""],
            318: ["part-a-iii-a-iii-residence-0-country", ""],
            319: ["part-a-iii-a-iii-residence-0-date-from", ""],
            320: ["part-a-iii-a-iii-residence-0-date-to", ""],
            321: ["part-a-iii-a-iii-residence-0-state", ""],
            322: ["part-a-iii-a-iii-residence-0-street", ""],
            323: ["part-a-iii-a-iii-residence-1-city", ""],
            324: ["part-a-iii-a-iii-residence-1-country", ""],
            325: ["part-a-iii-a-iii-residence-1-date-from", ""],
            326: ["part-a-iii-a-iii-residence-1-date-to", ""],
            327: ["part-a-iii-a-iii-residence-1-state", ""],
            328: ["part-a-iii-a-iii-residence-1-street", ""],
            329: ["part-a-iii-a-iii-residence-2-city", ""],
            330: ["part-a-iii-a-iii-residence-2-country", ""],
            331: ["part-a-iii-a-iii-residence-2-date-from", ""],
            332: ["part-a-iii-a-iii-residence-2-date-to", ""],
            333: ["part-a-iii-a-iii-residence-2-state", ""],
            334: ["part-a-iii-a-iii-residence-2-street", ""],
            335: ["part-a-iii-a-iii-residence-3-city", ""],
            336: ["part-a-iii-a-iii-residence-3-country", ""],
            337: ["part-a-iii-a-iii-residence-3-date-from", ""],
            338: ["part-a-iii-a-iii-residence-3-date-to", ""],
            339: ["part-a-iii-a-iii-residence-3-state", ""],
            340: ["part-a-iii-a-iii-residence-3-street", ""],
            341: ["part-a-iii-a-iii-residence-4-city", ""],
            342: ["part-a-iii-a-iii-residence-4-country", ""],
            343: ["part-a-iii-a-iii-residence-4-date-from", ""],
            344: ["part-a-iii-a-iii-residence-4-date-to", ""],
            345: ["part-a-iii-a-iii-residence-4-state", ""],
            346: ["part-a-iii-a-iii-residence-4-street", ""],
            347: ["part-a-iii-a-iii-residence-5-city", ""],
            348: ["part-a-iii-a-iii-residence-5-country", ""],
            349: ["part-a-iii-a-iii-residence-5-date-from", ""],
            350: ["part-a-iii-a-iii-residence-5-date-to", ""],
            351: ["part-a-iii-a-iii-residence-5-state", ""],
            352: ["part-a-iii-a-iii-residence-5-street", ""],
            353: ["part-a-iii-a-iii-residence-6-city", ""],
            354: ["part-a-iii-a-iii-residence-6-country", ""],
            355: ["part-a-iii-a-iii-residence-6-date-from", ""],
            356: ["part-a-iii-a-iii-residence-6-date-to", ""],
            357: ["part-a-iii-a-iii-residence-6-state", ""],
            358: ["part-a-iii-a-iii-residence-6-street", ""],
            359: ["part-a-iii-a-iii-residence-7-city", ""],
            360: ["part-a-iii-a-iii-residence-7-country", ""],
            361: ["part-a-iii-a-iii-residence-7-date-from", ""],
            362: ["part-a-iii-a-iii-residence-7-date-to", ""],
            363: ["part-a-iii-a-iii-residence-7-state", ""],
            364: ["part-a-iii-a-iii-residence-7-street", ""],
            365: ["part-a-iii-a-iii-residence-8-city", ""],
            366: ["part-a-iii-a-iii-residence-8-country", ""],
            367: ["part-a-iii-a-iii-residence-8-date-from", ""],
            368: ["part-a-iii-a-iii-residence-8-date-to", ""],
            369: ["part-a-iii-a-iii-residence-8-state", ""],
            370: ["part-a-iii-a-iii-residence-8-street", ""],
            371: ["part-a-iii-a-iii-sibling-0-ccob", ""],
            372: ["part-a-iii-a-iii-sibling-0-loc", ""],
            373: ["part-a-iii-a-iii-sibling-0-name", ""],
            374: ["part-a-iii-a-iii-sibling-1-ccob", ""],
            375: ["part-a-iii-a-iii-sibling-1-loc", ""],
            376: ["part-a-iii-a-iii-sibling-1-name", ""],
            377: ["part-a-iii-a-iii-sibling-2-ccob", ""],
            378: ["part-a-iii-a-iii-sibling-2-loc", ""],
            379: ["part-a-iii-a-iii-sibling-2-name", ""],
            380: ["part-a-iii-a-iii-sibling-3-ccob", ""],
            381: ["part-a-iii-a-iii-sibling-3-loc", ""],
            382: ["part-a-iii-a-iii-sibling-3-name", ""],
            383: ["part-a-iii-a-iii-sibling-4-ccob", ""],
            384: ["part-a-iii-a-iii-sibling-4-loc", ""],
            385: ["part-a-iii-a-iii-sibling-4-name", ""],
            386: ["part-a-iii-father-dec", ""],
            387: ["part-a-iii-mother-dec", ""],
            388: ["part-a-iii-sibling-0-dec", ""],
            389: ["part-a-iii-sibling-1-dec", ""],
            390: ["part-a-iii-sibling-2-dec", ""],
            391: ["part-a-iii-sibling-3-dec", ""],
            392: ["part-a-iii-sibling-4-dec", ""],
            393: ["part-b-b-crimeCheck", ""],
            394: ["part-b-b-crimeResp", ""],
            395: ["part-b-b-fearCheck", ""],
            396: ["part-b-b-fear-what", ""],
            397: ["part-b-b-fear-who", ""],
            398: ["part-b-b-fear-why", ""],
            399: ["part-b-b-harmCheck", ""],
            400: ["part-b-b-harm-what", ""],
            401: ["part-b-b-harm-when", ""],
            402: ["part-b-b-harm-who", ""],
            403: ["part-b-b-harm-why", ""],
            404: ["part-b-b-orgAssCheck", ""],
            405: ["part-b-b-orgAssResp", ""],
            406: ["part-b-b-orgPartCheck", ""],
            407: ["part-b-b-orgPartResp", ""],
            408: ["part-b-b-orgTortureCheck", ""],
            409: ["part-b-b-orgTortureResp", ""],
            410: ["part-b-reason", ""],
            411: ["part-c-c-causedHarm", ""],
            412: ["part-c-c-causedHarmCheck", ""],
            413: ["part-c-c-crimeComm", ""],
            414: ["part-c-c-crimeCommCheck", ""],
            415: ["part-c-c-inCountry", ""],
            416: ["part-c-c-lawfulStatusCheck", ""],
            417: ["part-c-c-lawfulStatusExp", ""],
            418: ["part-c-c-leftCountry", ""],
            419: ["part-c-c-leftCountryCheck", ""],
            420: ["part-c-c-oneYear", ""],
            421: ["part-c-c-oneYearCheck", ""],
            422: ["part-c-c-prevAppl", ""],
            423: ["part-c-c-prevApplCheck", ""],
            424: ["part-d-d-additionalApplnCheck", ""],
            425: ["part-d-d-assistanceCheck", ""],
            426: ["part-d-d-assistName-0", ""],
            427: ["part-d-d-assistName-1", ""],
            428: ["part-d-d-assistName-2", ""],
            429: ["part-d-d-assistName-3", ""],
            430: ["part-d-d-assistName-4", ""],
            431: ["part-d-d-completeName", ""],
            432: ["part-d-d-nativeName", ""],
            433: ["part-d-d-relationship-0", ""],
            434: ["part-d-d-relationship-1", ""],
            435: ["part-d-d-relationship-2", ""],
            436: ["part-d-d-relationship-3", ""],
            437: ["part-d-d-relationship-4", ""],
            438: ["part-d-d-reprCheck", ""],
            439: ["part-d-d-sign-date", ""],
            440: ["part-suppAB-suppAB-name", ""],
            441: ["part-suppAB-suppAB-part-0", ""],
            442: ["part-d-hiddenFileInput", ""],
            443: ["part-d-hiddenFileInput", ""],
            444: ["part-suppAB-suppAB-anumber", ""],
            445: ["part-d-hiddenFileInput", ""],
            446: ["part-suppAB-suppAB-date", ""],
            447: ["part-suppAB-suppAB-part-1", ""],
            448: ["part-suppAB-suppAB-ques-0", ""],
            449: ["part-suppAB-suppAB-ques-1", ""],
            450: ["part-suppAB-suppAB-resp-0", ""],
            451: ["part-suppAB-suppAB-resp-1", ""],
            452: ["part-a-i-a-i-telArea", ""],
            453: ["part-a-i-a-i-mailTelArea", ""],

        }
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


class Dolores():
    def __init__(self):
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.RELO_ASSISTANT_ID = os.getenv('RELO_ASSISTANT_ID')
        self.DOLORES_ASSISTANT_ID = os.getenv('DOLORES_ASSISTANT_ID')
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

    def assistant(self, user_input, assistant='relo'):
        assistant_id = {
            'relo': self.RELO_ASSISTANT_ID,
            'dolores': self.DOLORES_ASSISTANT_ID,
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

    async def chat(self, user_input, user, assistant='relo'):
        self.user_input = user_input
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


@app.get('/test/')
async def test_func():
    return {'test': 'successful'}

if __name__ == "__main__":
    host = '0.0.0.0'
    uvicorn.run("backend:app", host=host, reload=True)
