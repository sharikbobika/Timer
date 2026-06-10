from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'timer-app-secret-key-2026'

# Achievement definitions
ACHIEVEMENTS = {
    'first_try': {
        'id': 'first_try',
        'title': 'Попробуй сервис',
        'description': 'Установите свой первый таймер',
        'icon': '🎮',
        'color': '#FFD700',  # Gold
        'hidden': False
    },
    'speed_demon': {
        'id': 'speed_demon',
        'title': 'Скоро дело!',
        'description': 'Установите таймер менее чем на 1 минуту',
        'icon': '⚡',
        'color': '#FF6B6B',  # Red
        'hidden': False
    },
    'marathon': {
        'id': 'marathon',
        'title': 'Марафон',
        'description': 'Установите таймер более чем на 24 часа',
        'icon': '🏃',
        'color': '#4ECDC4',  # Teal
        'hidden': False
    },
    'persistence': {
        'id': 'persistence',
        'title': 'Настойчивость',
        'description': 'Используйте паузу 5 раз в одной сессии',
        'icon': '⏸️',
        'color': '#95E1D3',  # Mint
        'hidden': False
    },
    'collector': {
        'id': 'collector',
        'title': 'Коллекционер',
        'description': 'Разблокируйте 5 достижений',
        'icon': '🏆',
        'color': '#F38181',  # Pink
        'hidden': False
    },
    'time_master': {
        'id': 'time_master',
        'title': 'Мастер времени',
        'description': 'Дождитесь окончания таймера без паузы',
        'icon': '🕐',
        'color': '#AA96DA',  # Purple
        'hidden': False
    }
}

def init_session_achievements():
    """Инициализируем достижения в сессии пользователя"""
    if 'achievements' not in session:
        session['achievements'] = []
        session['pause_count'] = 0
        session['timer_completed_without_pause'] = False

@app.before_request
def before_request():
    init_session_achievements()

@app.route('/')
def index():
    init_session_achievements()
    return render_template('index.html')

@app.route('/api/achievements', methods=['GET'])
def get_achievements():
    """Получить список всех достижений и какие разблокированы"""
    unlocked = session.get('achievements', [])
    
    achievements_list = []
    for ach_id, ach_data in ACHIEVEMENTS.items():
        achievement = ach_data.copy()
        achievement['unlocked'] = ach_id in unlocked
        achievements_list.append(achievement)
    
    return jsonify({
        'achievements': achievements_list,
        'total_unlocked': len(unlocked)
    })

@app.route('/api/unlock-achievement', methods=['POST'])
def unlock_achievement():
    """Разблокировать достижение"""
    data = request.json
    achievement_id = data.get('id')
    
    if achievement_id not in ACHIEVEMENTS:
        return jsonify({'error': 'Achievement not found'}), 404
    
    achievements = session.get('achievements', [])
    
    if achievement_id not in achievements:
        achievements.append(achievement_id)
        session['achievements'] = achievements
        session.modified = True
        
        # Проверяем, нужно ли разблокировать "collector"
        if len(achievements) == 5 and 'collector' not in achievements:
            achievements.append('collector')
            session['achievements'] = achievements
            session.modified = True
            return jsonify({
                'unlocked': True,
                'achievement': ACHIEVEMENTS[achievement_id],
                'bonus_unlock': 'collector'
            })
        
        return jsonify({
            'unlocked': True,
            'achievement': ACHIEVEMENTS[achievement_id]
        })
    
    return jsonify({'unlocked': False})

@app.route('/api/timer-started', methods=['POST'])
def timer_started():
    """Вызывается когда пользователь установил таймер"""
    data = request.json
    target_time = data.get('target_time')  # milliseconds
    
    achievements_to_unlock = []
    
    # First try
    if 'first_try' not in session.get('achievements', []):
        achievements_to_unlock.append('first_try')
    
    # Speed demon - менее 1 минуты (60000 ms)
    if target_time and target_time < 60000:
        if 'speed_demon' not in session.get('achievements', []):
            achievements_to_unlock.append('speed_demon')
    
    # Marathon - более 24 часов (86400000 ms)
    if target_time and target_time > 86400000:
        if 'marathon' not in session.get('achievements', []):
            achievements_to_unlock.append('marathon')
    
    # Reset timer_completed flag
    session['timer_completed_without_pause'] = True
    session.modified = True
    
    return jsonify({'new_achievements': achievements_to_unlock})

@app.route('/api/timer-paused', methods=['POST'])
def timer_paused():
    """Вызывается когда пользователь паузит таймер"""
    session['timer_completed_without_pause'] = False
    session['pause_count'] = session.get('pause_count', 0) + 1
    session.modified = True
    
    achievements_to_unlock = []
    
    # Persistence - 5 пауз
    if session['pause_count'] >= 5:
        if 'persistence' not in session.get('achievements', []):
            achievements_to_unlock.append('persistence')
    
    return jsonify({'new_achievements': achievements_to_unlock})

@app.route('/api/timer-completed', methods=['POST'])
def timer_completed():
    """Вызывается когда таймер дошел до нуля"""
    achievements_to_unlock = []
    
    # Time master - дождался без паузы
    if session.get('timer_completed_without_pause', False):
        if 'time_master' not in session.get('achievements', []):
            achievements_to_unlock.append('time_master')
    
    return jsonify({'new_achievements': achievements_to_unlock})

@app.route('/api/timer-reset', methods=['POST'])
def timer_reset():
    """Вызывается когда пользователь сбросил таймер"""
    session['pause_count'] = 0
    session['timer_completed_without_pause'] = False
    session.modified = True
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
