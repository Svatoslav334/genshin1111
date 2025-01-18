from flask import Flask, render_template, request
import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime

app = Flask(__name__)

# Функция для декодирования MIME-заголовков
def decode_mime_header(header):
    decoded_header, encoding = decode_header(header)[0]
    if isinstance(decoded_header, bytes):
        return decoded_header.decode(encoding if encoding else 'utf-8')
    return decoded_header

# IMAP-серверы для разных почтовых сервисов
imap_servers = {
    "rambler": {
        "server": "imap.rambler.ru",
        "port": 993
    },
    "firstmail": {
        "server": "imap.firstmail.ltd",
        "port": 993
    }
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email_user = request.form['email']  # Получаем email из формы
        password_user = request.form['password']  # Получаем пароль из формы
        mail_service = request.form['mail_service']  # Получаем выбранный почтовый сервис
        
        # Получаем настройки IMAP-сервера в зависимости от выбранного сервиса
        imap_server = imap_servers.get(mail_service, {}).get("server")
        imap_port = imap_servers.get(mail_service, {}).get("port")

        if not imap_server:
            return "Invalid mail service selected"

        try:
            # Подключаемся к выбранному серверу
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(email_user, password_user)

            # Открываем почтовый ящик
            mail.select("inbox")
            
            # Получаем список всех писем
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()
            
            # Получаем все письма
            emails = []
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_mime_header(msg["Subject"])
                        from_ = decode_mime_header(msg.get("From"))
                        date = parsedate_to_datetime(msg["Date"])  # Получаем дату письма
                        emails.append({"subject": subject, "from": from_, "date": date})
            
            # Сортируем письма по дате (самое новое первое)
            emails.sort(key=lambda x: x["date"], reverse=True)
            
            return render_template("index.html", emails=emails)
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    return render_template("index.html", emails=None)

if __name__ == "__main__":
    app.run(debug=True)
