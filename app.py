from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random
from sqlalchemy import func


app = Flask(__name__)

# Настройка базы данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db = SQLAlchemy(app)


# Модель агента (таблица Agent)
class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codename = db.Column(db.String(100), nullable=False, unique=True, index=True)
    contact_number = db.Column(db.String(32), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    access_level = db.Column(db.Enum('Секретно', 'Очень секретно', 'Совершенно секретно',
                                     name='access_level_enum'), nullable=False, default='Секретно')

    def __repr__(self):
        return f"<Agent {self.codename}, contact number: {self.contact_number}, " \
               f"email: {self.email}, access level: {self.access_level}>"


# Создаем таблицу в базе данных
with app.app_context():
    db.create_all()


# Главная страница: список всех агентов, поиск по кодовому имени и фильтр по уровню доступа
@app.route('/')
@app.route('/agents')
def get_agents():
    q = request.args.get('q', '').strip()  # значение из строки поиска
    level = request.args.get('level', '').strip()
    query = Agent.query
    if q:
        query = query.filter(Agent.codename.ilike(f"%{q}%"))
    if level:
        query = query.filter(Agent.access_level == level)

    agents = query.all()
    levels = ['Секретно', 'Очень секретно', 'Совершенно секретно']
    return render_template('agents.html', agents=agents, q=q, level=level, levels=levels)


# Добавление нового агента
@app.route('/add', methods=['GET', 'POST'])
def add_agent():
    if request.method == 'POST':
        codename = request.form['codename']
        contact_number = request.form['contact_number']
        email = request.form['email']
        access_level = request.form['access_level']
        if codename.strip() and contact_number.strip() and email.strip() and access_level.strip():  # Проверяем, что строка не пустая
            new_agent = Agent(codename=codename, contact_number=contact_number,
                              email=email, access_level=access_level)
            db.session.add(new_agent)
            db.session.commit()
        return redirect(url_for('get_agents'))
    return render_template('add_agent.html')


ADJ = ["Shadow", "Silent", "Crimson", "Midnight", "Phantom", "Iron",
       "Silver", "Ghost", "Night", "Storm", "Hidden", "Cold", "Dark"]

NOUN = ["Fox", "Viper", "Raven", "Wolf", "Falcon", "Widow",
        "Cobra", "Jackal", "Panther", "Warden", "Mantis"]


def generate_unique_codename(max_attempts=20):
    for _ in range(max_attempts):
        name = f"{random.choice(ADJ)} {random.choice(NOUN)}"
        exists = Agent.query.filter(func.lower(Agent.codename) == name.lower()).first()
        if not exists:
            return name
    return f"{random.choice(ADJ)} {random.choice(NOUN)}"


# Генерация случайного кодового имени
@app.get('/api/generate_codename')
def api_generate_codename():
    name = generate_unique_codename()
    return {"codename": name}


# Просмотр досье
@app.route('/agent/<int:id>', methods=['GET'])
def agent_dossier(id):
    agent = Agent.query.get_or_404(id)  # Получаем досье по ID
    return render_template('agent_dossier.html', agent=agent)


# Редактирование досье
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_agent(id):
    agent = Agent.query.get_or_404(id)  # Получаем досье по ID
    if request.method == 'POST':
        codename = request.form['codename']
        contact_number = request.form['contact_number']
        email = request.form['email']
        access_level = request.form['access_level']
        if codename.strip() and contact_number.strip() and email.strip() and access_level.strip():  # Проверяем, что строка не пустая
            agent.codename = codename
            agent.contact_number = contact_number
            agent.email = email
            agent.access_level = access_level
            db.session.commit()
        return redirect(url_for('get_agents'))
    return render_template('edit_agent.html', agent=agent)


# Удаление агента из базы
@app.route('/delete/<int:id>')
def delete_agent(id):
    agent = Agent.query.get_or_404(id)  # Получаем досье по ID
    db.session.delete(agent)  # Удаляем из базы
    db.session.commit()  # Подтверждаем изменения
    return redirect(url_for('get_agents'))


# Секретный режим - удаление всех данных
@app.route('/nuke', methods=['POST'])
def nuke_all():
    db.session.query(Agent).delete()
    db.session.commit()
    return redirect(url_for('get_agents'))


# Запуск сервера
if __name__ == "__main__":
    app.run(debug=True)
