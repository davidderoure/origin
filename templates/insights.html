{% extends "base.html" %}

{% block content %}
<h2>📊 Insights & Patterns</h2>

{% if user_data %}
<h3>Your Reading Journey</h3>

<div class="card">
    <h4>Mood History (Last 10 entries)</h4>
    <table>
        <thead>
            <tr>
                <th>Time</th>
                <th>Mood</th>
            </tr>
        </thead>
        <tbody>
            {% for time, mood in user_data.mood_history %}
            <tr>
                <td>{{ time }}</td>
                <td>{{ mood }}/10</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<div class="card">
    <h4>Theme Preferences</h4>
    <table>
        <thead>
            <tr>
                <th>Theme</th>
                <th>Preference Score</th>
            </tr>
        </thead>
        <tbody>
            {% for theme, score in user_data.theme_scores[:5] %}
            <tr>
                <td><span class="theme-badge">{{ theme }}</span></td>
                <td>{{ "%.2f"|format(score) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% if user_data.sequences %}
<div class="card">
    <h4>Your Story Sequences (Last 10)</h4>
    <table>
        <thead>
            <tr>
                <th>From Story</th>
                <th>To Story</th>
                <th>Mood Change</th>
            </tr>
        </thead>
        <tbody>
            {% for seq in user_data.sequences %}
            <tr>
                <td>{{ seq.from }}</td>
                <td>{{ seq.to }}</td>
                <td>
                    {% if seq.mood_delta %}
                        <strong style="color: {% if seq.mood_delta > 0 %}#28a745{% else %}#dc3545{% endif %}">
                            {{ "%+.2f"|format(seq.mood_delta) }}
                        </strong>
                    {% else %}
                        N/A
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}
{% endif %}

<h3>Global Story Patterns</h3>

{% for story_title, data in insights.global_transitions.items() %}
    {% if data.best_next %}
    <div class="card">
        <h4>After "{{ story_title }}"</h4>
        
        {% if data.best_next %}
        <p><strong>Best next stories:</strong></p>
        <ul>
            {% for next_title, effect in data.best_next %}
            <li>
                {{ next_title }} 
                <span style="color: {% if effect > 0 %}#28a745{% else %}#dc3545{% endif %}">
                    (mood {{ "%+.2f"|format(effect) }})
                </span>
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if data.best_next_themes %}
        <p><strong>Best next themes:</strong></p>
        <ul>
            {% for theme, effect in data.best_next_themes.items() %}
            <li>
                <span class="theme-badge">{{ theme }}</span>
                <span style="color: {% if effect > 0 %}#28a745{% else %}#dc3545{% endif %}">
                    (mood {{ "%+.2f"|format(effect) }})
                </span>
            </li>
            {% endfor %}
        </ul>
        {% endif %}
    </div>
    {% endif %}
{% endfor %}

<div style="margin-top: 30px;">
    <a href="{{ url_for('index') }}" class="btn btn-secondary">← Back to Home</a>
</div>
{% endblock %}
