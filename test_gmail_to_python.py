__author__ = 'abhishek.edu19@gmail.com'
import imaplib
import json
import email
import argparse
import mysql.connector
from datetime import datetime, timedelta
from dateutil import parser as date_parser





imapHostServer = 'imap.gmail.com'
imapUserEmail = 'xxxx@gmail.com'
imapPassword = 'xxxx'

def main(params):
    try:
        mail = imap_server_connect(imapHostServer, imapUserEmail, imapPassword)
    except Exception as e:
        print(e)
    iterate_per_mail(mail=mail)

def iterate_per_mail(mail):
    search_criteria = search_criterias(mail, category_to_remove="Promotions")
    status, messages = mail.search(None, search_criteria)

    # Get the list of message IDs
    message_ids = messages[0].split()

    # Iterate through the emails and process them
    for message_id in message_ids:
        status, msg_data = mail.fetch(message_id, '(RFC822)')
        email_message = email.message_from_bytes(msg_data[0][1])

        # Process the email message and store relevant information in the database
        process_and_store(email_message)

    # Logout and close the connection
    mail.logout()



# Function to process and store email information in the database
def process_and_store(email_message):
    # Extract information from the email message
    subject = email_message["Subject"]
    sender = email_message["From"]
    date = email_message["Date"]
    body = ""

    # Check if the email message is multipart (contains both text and attachments)
    if email_message.is_multipart():
        # Iterate through the parts of the email
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Extract the email body (text/plain)
            if "text/plain" in content_type and "attachment" not in content_disposition:
                body = part.get_payload(decode=True).decode()


    email_data = {
        "Subject": subject,
        "Sender": sender,
        "Date": date,
        "Body": body
    }
    # Convert the dictionary to JSON string
    json_data = json.dumps(email_data, ensure_ascii=False, indent=2)
    print(json_data)
    # Replace this with the actual code for storing the data in your database.
    print("Storing the data in the database...")
    write_to_db(json_data)



def imap_server_connect(imapHostServer, imapUserEmail, imapPassword):

    """ Connect to the IMAP server """
    mail = imaplib.IMAP4_SSL(imapHostServer)
    mail.login(imapUserEmail, imapPassword)
    return mail


def get_yesterday_date():
    todays_date = datetime.now()
    yest_date = todays_date - timedelta(days=1)
    yest_date_formatted = yest_date.strftime("%d-%b-%Y")
    print(yest_date_formatted)
    return '12-Jul-2023'#yest_date_formatted



def search_criterias(mail, folder='inbox', category_to_remove="Promotions"):
    imap_server_connect(imapHostServer, imapUserEmail, imapPassword)
    # Select the inbox folder
    mail.select(folder)
    category_to_remove = category_to_remove
    # Set the desired date (replace with your desired date format)
    desired_date = get_yesterday_date()  # Format: DD-Mon-YYYY

    # Search for emails received since the desired date and without the "promotions" label
    return f'SINCE "{desired_date}" NOT HEADER "X-Gmail-Labels" "{category_to_remove}"'
def parse_email_date(date_str):
    # Parse the email date without the timezone information
    email_date_obj = parse(date_str.split(" (")[0])
    return email_date_obj.strftime("%Y-%m-%d %H:%M:%S %z")

def write_to_db(json_data):
    # Connect to the database (change the database name if needed)
    try:
        connection = mysql.connector.connect(
            host='Mavericks-MacBook-Pro.local',
            database='gmail_data',
            user='root',
            password='password'
        )

        cursor = connection.cursor()

        email_data = json.loads(json_data)
        email_date_obj = date_parser.parse(email_data['Date'])
        formatted_date = email_date_obj.strftime("%Y-%m-%d %H:%M:%S")

        # Prepare the SQL query to insert data into the mail_data table
        insert_query = "INSERT INTO mail_data (Subject, mail_Date, Body, sync_date) " \
                       "VALUES (%s, %s, %s, NOW())"
        values = (email_data['Subject'], formatted_date, email_data['Body'], )

        cursor.execute(insert_query, values)
        connection.commit()

        cursor.execute("SELECT COUNT(*) FROM mail_data")
        print("Number of rows after data insertion:", cursor.fetchone()[0])

        # Close the cursor and connection
        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print("Error while connecting to MySQL:", e)

    print("Data inserted successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #parser.add_argument("--desired_date", type=str, help="Desired date (e.g., 12-Jul-2023)")
    parser.add_argument("--category_to_remove", type=str, help="Category to remove (e.g., Promotions)")
    args = parser.parse_args()
    try:
        main(args)
    except Exception as e:
        print(e)




# CREATE TABLE gmail_data.mail_data
# (ID INT AUTO_INCREMENT PRIMARY KEY, Subject VARCHAR(1000),
# mail_Date DATE, Body VARCHAR(16382), sync_date DATETIME DEFAULT CURRENT_TIMESTAMP);