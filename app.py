from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import json
import os

# Import your recommender system
from rec2 import StoryRecommender, AnalyticsEvent, MoodScore

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Initialize recommender with sample stories
recommender = StoryRecommender(
    event_half_life_days=30.0,
    mood_half_life_days=14.0,
    transition_window_minutes=1440.0
)

# Add sample stories
def initialize_stories():
    recommender.add_story("story1", "The Happy Garden", "nature", 
                         ["uplifting", "peaceful", "hopeful"])
    recommender.add_story("story2", "Dark Mystery", "mystery", 
                         ["thriller", "suspense", "intense"])
    recommender.add_story("story3", "Summer Joy", "nature", 
                         ["uplifting", "warm", "cheerful"])
    recommender.add_story("story4", "The Detective", "mystery", 
                         ["investigation", "clever", "intriguing"])
    recommender.add_story("story5", "Mountain Peace", "nature", 
                         ["meditative", "calm", "serene"])
    recommender.add_story("story6", "City Lights", "urban", 
                         ["energetic", "modern", "vibrant"])
    recommender.add_story("story7", "Ocean Waves", "nature", 
                         ["calming", "peaceful", "soothing"])
    recommender.add_story("story8", "Night Cafe", "urban", 
                         ["contemplative", "cozy", "intimate"])
    recommender.add_story("story9", "Forest Whispers", "nature", 
                         ["mystical", "peaceful", "enchanting"])
    recommender.add_story("story10", "Urban Pulse", "urban", 
                         ["exciting", "fast-paced", "dynamic"])

initialize_stories()

# Story content (for demo purposes)
STORY_CONTENT = {
    "story1": """
        In a small corner of the city, there lived a garden that seemed to know secrets. 
        Every morning, the flowers would bloom with such radiance that passersby would stop 
        and smile, forgetting their worries for just a moment. Maria tended this garden with 
        love, and the garden returned that love tenfold, bringing joy to everyone who visited.
    """,
    "story2": """
        The clock struck midnight as Detective Chen entered the abandoned mansion. 
        The case had gone cold three years ago, but new evidence suggested the answers 
        were hidden here all along. Shadows danced on the walls, and every creaking 
        floorboard seemed to whisper secrets that had been buried for too long.
    """,
    "story3": """
        Summer arrived like a promise kept. The days were long and golden, filled with 
        laughter and the taste of fresh strawberries. Children played in the sprinklers, 
        and neighbors gathered for evening barbecues. It was a time when everything felt 
        possible, and happiness was as simple as sunshine on your face.
    """,
    "story4": """
        Inspector Morris had solved countless cases, but this one was different. 
        The clues formed a pattern that seemed almost too clever, as if the perpetrator 
        wanted to be caught—but only by someone smart enough to deserve it. Each piece 
        of evidence led to another question, and Morris felt both frustrated and thrilled.
    """,
    "story5": """
        High above the valley, where the air was thin and pure, there stood a small cabin. 
        Here, time moved differently. The mountains spoke in the language of wind and stone, 
        teaching patience to those who would listen. Sarah came here to find peace, 
        and the mountains welcomed her like an old friend.
    """,
    "story6": """
        The city never slept, and neither did Alex. From rooftop parties to late-night 
        food trucks, from street art to underground music venues, the urban landscape 
        was an endless adventure. Neon lights reflected in rain-puddles, and every corner 
        held a new story waiting to unfold.
    """,
    "story7": """
        The waves rolled in with hypnotic rhythm, each one carrying away a little more 
        of yesterday's worries. Elena walked barefoot along the shore, letting the cool 
        water wash over her feet. The ocean had always been her sanctuary, a place where 
        she could breathe deeply and remember what truly mattered.
    """,
    "story8": """
        The café was a haven in the concrete jungle. Warm light spilled from its windows 
        onto the dark street outside. Inside, people sat quietly with their thoughts, 
        their books, their late-night conversations. The barista knew everyone's order 
        by heart, and the coffee was always perfect.
    """,
    "story9": """
        Deep in the ancient forest, where sunlight filtered through a canopy of leaves, 
        there was magic in the air. Not the flashy kind from storybooks, but the subtle 
        magic of growth, renewal, and connection. The trees whispered stories to those 
        who knew how to listen, and the forest held mysteries that time had forgotten.
    """,
    "story10": """
        The city's heartbeat was fastest here, in the downtown core where ambition 
        and energy collided. Jordan thrived in this environment, drawing inspiration 
        from the constant motion, the diverse faces, the sense that anything could happen. 
        This was where dreams were made, where the future was being written in real-time.
    """
}

def get_user_id():
    """Get or create user ID from session"""
    if 'user_id' not in session:
        session['user_id'] = f"demo_user_{datetime.now().timestamp()}"
    return session['user_id']

@app.route('/')
def index():
    """Home page - mood check and story recommendations"""
    user_id = get_user_id()
    
    # Get user profile if exists
    user = recommender.users.get(user_id)
    current_mood = user.current_mood.value if user and user.current_mood else None
    recommendation_mix = user.recommendation_mix if user else 0.5
    
    # Get user stats
    stats = {
        'stories_read': len(user.viewed_stories) if user else 0,
        'stories_completed': len(user.completed_stories) if user else 0,
        'favorites': len(user.favorited_stories) if user else 0,
        'mood_trend': user._mood_trend if user else None,
        'last_completed': None
    }
    
    if user and user.last_completed_story and user.last_completed_story in recommender.stories:
        stats['last_completed'] = recommender.stories[user.last_completed_story].title
    
    return render_template('index.html', 
                         current_mood=current_mood,
                         recommendation_mix=recommendation_mix,
                         stats=stats,
                         user_id=user_id)

@app.route('/set_mood', methods=['POST'])
def set_mood():
    """Set user's current mood"""
    user_id = get_user_id()
    mood_value = float(request.form['mood'])
    
    event = AnalyticsEvent(
        user_id,
        'mood_general',
        datetime.now(),
        mood_score=mood_value
    )
    recommender.add_event(event)
    
    return redirect(url_for('index'))

@app.route('/set_slider', methods=['POST'])
def set_slider():
    """Set recommendation mix slider"""
    user_id = get_user_id()
    position = float(request.form['position'])
    
    event = AnalyticsEvent(
        user_id,
        'slider_position',
        datetime.now(),
        position=position
    )
    recommender.add_event(event)
    
    return redirect(url_for('index'))

@app.route('/recommendations')
def recommendations():
    """Show personalized recommendations"""
    user_id = get_user_id()
    
    # Get recommendations
    recs = recommender.get_recommendations(user_id, n_recommendations=8)
    
    # Prepare recommendation data
    rec_data = []
    for story_id, score in recs:
        story = recommender.stories[story_id]
        
        # Get reasons for recommendation
        reasons = []
        
        # Check if it's a good follow-up to last completed story
        user = recommender.users.get(user_id)
        if user and user.last_completed_story:
            last_story = recommender.stories.get(user.last_completed_story)
            if last_story:
                if story_id in last_story.best_next_stories:
                    effect = last_story.best_next_stories[story_id]
                    reasons.append(f"Great follow-up to '{last_story.title}' (mood effect: {effect:+.1f})")
                
                if story.theme in last_story.best_next_themes:
                    theme_effect = last_story.best_next_themes[story.theme]
                    reasons.append(f"Theme transition works well (effect: {theme_effect:+.1f})")
        
        # Check mood effectiveness
        if user and user.current_mood:
            mood_range = recommender._get_mood_range(user.current_mood.value)
            if mood_range in story.mood_effectiveness:
                effectiveness = story.mood_effectiveness[mood_range]
                if effectiveness > 0.5:
                    reasons.append(f"Works well for your current mood")
        
        # Check if favorited similar stories
        if user and user.favorited_stories:
            for fav_id in user.favorited_stories:
                similarity = recommender._story_similarity(story_id, fav_id)
                if similarity > 0.5 and fav_id in recommender.stories:
                    reasons.append(f"Similar to '{recommender.stories[fav_id].title}' (favorite)")
                    break
        
        rec_data.append({
            'id': story_id,
            'title': story.title,
            'theme': story.theme,
            'tags': story.tags,
            'score': score,
            'reasons': reasons,
            'avg_mood_change': story.avg_mood_change
        })
    
    return render_template('recommendations.html', recommendations=rec_data)

@app.route('/story/<story_id>')
def view_story(story_id):
    """View a story"""
    user_id = get_user_id()
    
    if story_id not in recommender.stories:
        return redirect(url_for('index'))
    
    story = recommender.stories[story_id]
    content = STORY_CONTENT.get(story_id, "Story content not available.")
    
    # Record view event
    event = AnalyticsEvent(
        user_id,
        'view',
        datetime.now(),
        story_id=story_id
    )
    recommender.add_event(event)
    
    # Check if already completed
    user = recommender.users.get(user_id)
    already_completed = user and story_id in user.completed_stories
    
    return render_template('story.html', 
                         story=story, 
                         content=content,
                         already_completed=already_completed)

@app.route('/complete_story/<story_id>', methods=['POST'])
def complete_story(story_id):
    """Mark story as completed"""
    user_id = get_user_id()
    
    event = AnalyticsEvent(
        user_id,
        'complete',
        datetime.now(),
        story_id=story_id
    )
    recommender.add_event(event)
    
    return redirect(url_for('mood_after_story', story_id=story_id))

@app.route('/mood_after/<story_id>')
def mood_after_story(story_id):
    """Ask for mood after completing a story"""
    story = recommender.stories.get(story_id)
    if not story:
        return redirect(url_for('index'))
    
    user_id = get_user_id()
    user = recommender.users.get(user_id)
    mood_before = user.current_mood.value if user and user.current_mood else None
    
    return render_template('mood_after.html', 
                         story=story, 
                         mood_before=mood_before)

@app.route('/submit_mood_after/<story_id>', methods=['POST'])
def submit_mood_after(story_id):
    """Submit mood after story"""
    user_id = get_user_id()
    mood_value = float(request.form['mood'])
    
    event = AnalyticsEvent(
        user_id,
        'mood_after',
        datetime.now(),
        story_id=story_id,
        mood_score=mood_value
    )
    recommender.add_event(event)
    
    return redirect(url_for('recommendations'))

@app.route('/favorite/<story_id>', methods=['POST'])
def favorite_story(story_id):
    """Add story to favorites"""
    user_id = get_user_id()
    
    event = AnalyticsEvent(
        user_id,
        'favorite',
        datetime.now(),
        story_id=story_id
    )
    recommender.add_event(event)
    
    return redirect(url_for('view_story', story_id=story_id))

@app.route('/insights')
def insights():
    """Show insights about sequences and patterns"""
    user_id = get_user_id()
    
    # Get sequence insights
    insights_data = recommender.get_sequence_insights(user_id)
    
    # Get user-specific data
    user = recommender.users.get(user_id)
    user_data = None
    
    if user:
        # Get theme preferences
        theme_scores = user._get_decayed_theme_scores(datetime.now())
        
        user_data = {
            'mood_history': [(ts.strftime('%Y-%m-%d %H:%M'), mood.value) 
                           for ts, mood in user.mood_history[-10:]],
            'theme_scores': sorted(theme_scores.items(), key=lambda x: x[1], reverse=True),
            'sequences': insights_data.get('user_sequences', [])[-10:]
        }
    
    return render_template('insights.html', 
                         insights=insights_data,
                         user_data=user_data)

@app.route('/reset')
def reset():
    """Reset the demo (clear session)"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
