import mailtrap

mailtoken = "85622feada60362e972757f36145fadc"

def email(to, subject, message):
    mail = mailtrap.Mail(
        sender = mailtrap.Address(email = "hello@demomailtrap.co", name = "FLASK_API"),
        to = [mailtrap.Address(email = to)],
        subject = subject,
        text = message,
        category = "mailtrap integration test"
    )
    client = mailtrap.MailtrapClient(token = mailtoken)
    response = client.send(mail)
    
    print("This is mailtrap---------------------------------------------------------------------------------------")
    print(response)
    
# email("levy4star@gmail.com", "Testing API", "Need money for porsche")