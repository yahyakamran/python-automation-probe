import os.path
import io

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from googleapiclient.http import MediaIoBaseDownload

import qrcode


#service account token file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly',
          'https://www.googleapis.com/auth/drive']
TOKEN_FILE = 'key.json'


# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = "1tcD0VhJChXluqqE5TQRuzuvP578rQevdBWXdSrfts4c"
RANGE_NAME = "'Form Responses 1'!A1:V49"

def getApplicant(creds):
    applicants = []
    try:
        print("INFO: Extracting data from google spread sheet")
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()
        result = (
                sheet.values().
                get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).
                execute()
        )
        values = result.get("values", [])

        if not values:
            print("INFO: No data found")
            return [];
        print("INFO: Extracted data from google spread sheet")

        for i in range(1, len(values)):
            team_email = values[i][2]
            team_name = values[i][3]
            no_of_members = values[i][4]
            members_emails, members_rollnos, members_images, team_logo = "","","",""
            if(no_of_members == '2'):
                members_emails = [ values[i][5], values[i][6]]
                members_rollnos = [ values[i][7], values[i][8]]
                members_images = [ values[i][9], values[i][10]]
                team_logo = values[i][11]
            if(no_of_members == '3'):
                members_emails = [ values[i][12], values[i][13], values[i][14]]
                members_rollnos = [ values[i][15], values[i][16], values[i][17]]
                members_images = [ values[i][18], values[i][19], values[i][20]]
                team_logo = values[i][21]
            applicant = [team_email, team_name, no_of_members, members_emails, members_rollnos, members_images, team_logo]
            applicants.append(applicant)
            print("INFO: New Team Added\nName: "+team_name+" Email: "+team_email)
        return applicants

    except HttpError as err:
        print(err)
        return []



def main():
    creds = None

    if os.path.exists(TOKEN_FILE):
        print("INFO: Checking credentials")
        creds = service_account.Credentials.from_service_account_file(
                TOKEN_FILE, scopes=SCOPES)

    if not creds:
        print("ERROR: Credentials are required")
        exit(1)
    print("INFO: Connection Succcessfull")

    applicants = getApplicant(creds);
    if len(applicants) == 0:
        exit(1);

    os.makedirs("./build", exist_ok=True)
    print("INFO: Making build directory")
    if not os.path.exists("Inter-VariableFont_opsz,wght.ttf"):
        print("ERROR: Font are required")
        exit(1)

    if not os.path.exists("background.jpeg"):
        print("ERROR: Base image are required")
        exit(1)

    font = ImageFont.truetype("Inter-VariableFont_opsz,wght.ttf", 44)
    font_s = ImageFont.truetype("Inter-VariableFont_opsz,wght.ttf", 24)

    gdrive_service = build("drive", "v3", credentials=creds)
    os.makedirs("./temp", exist_ok=True)
    print("INFO: Making temp directory")


    for applicant in applicants:
        ## loading background pic
        bg_image = Image.open("background.jpeg")
        bg_image = bg_image.resize((640,1020))
        draw = ImageDraw.Draw(bg_image)

        ## Downloading team logo
        id = applicant[6].split("?id=")[1]
        request = gdrive_service.files().get_media(fileId = id)
        destination_path = "./temp/"+applicant[1]+"_logo.jpeg";
        fh = io.FileIO(destination_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _ , done = downloader.next_chunk()
        print(f"INFO: File downloaded to {destination_path}")

        ## Pasting logo in background image
        logo_image = Image.open(destination_path)
        logo_image = logo_image.resize((228,220))
        bg_image.paste(logo_image, (63,330))

        ## Writing team name on background image
        _, _, w, h = draw.textbbox((0, 0), applicant[1], font=font)
        draw.text(((bg_image.width - w)/2, bg_image.height/1.6),
                  applicant[1],(255,255,255),font=font)
        draw.text(((bg_image.width - w)/2, (bg_image.height/1.6 + h+5)),
                  "team name",(80,190,203),font=font_s)
        #draw.text((70, 303),".",(0,0,0),font=font)
        #draw.text((270, 495),".",(0,0,0),font=font)
        #draw.text((345, 303),".",(0,0,0),font=font)
        #draw.text((545, 495),".",(0,0,0),font=font)

        print("INFO: Generating Qr code")
        qr = qrcode.make(applicant)
        qr_path = "./temp/"+applicant[1]+"_qr.jpeg"
        qr.save(qr_path);
        qr_image = Image.open(qr_path)
        qr_image = qr_image.resize((228,220))
        bg_image.paste(qr_image, (335,330))

        image_name = "./build/"+applicant[1]+".jpeg";
        bg_image.save(image_name)
        print("INFO: Saving "+ image_name)




if __name__ == "__main__":
    main()

