# app.py - Flask web server for Story Recommender Demo

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
    recommender.add_story("story1", "The Alfred Jewel", "ancient", 
                         ["mysterious", "royal", "craftsmanship"])
    recommender.add_story("story2", "The Last Dodo", "natural", 
                         ["extinct", "haunting", "loss"])
    recommender.add_story("story3", "Guy Fawkes' Lantern", "medieval", 
                         ["conspiracy", "history", "rebellion"])
    recommender.add_story("story4", "The Scorpion Macehead", "ancient", 
                         ["Egyptian", "powerful", "discovery"])
    recommender.add_story("story5", "Powhatan's Mantle", "cultural", 
                         ["ceremonial", "heritage", "connection"])
    recommender.add_story("story6", "The Abingdon Sword", "medieval", 
                         ["warrior", "crafted", "legendary"])
    recommender.add_story("story7", "Tradescant's Ark", "natural", 
                         ["curious", "wondrous", "collection"])
    recommender.add_story("story8", "The Parian Marble", "ancient", 
                         ["chronological", "scholarly", "timeless"])
    recommender.add_story("story9", "Ceremonial Axes", "cultural", 
                         ["ritual", "spiritual", "ancestral"])
    recommender.add_story("story10", "Einstein's Blackboard", "scientific", 
                         ["exciting", "fast-paced", "dynamic"])

initialize_stories()

# Story content (for demo purposes)
STORY_CONTENT = {
    "story1": """
        In the Ashmolean Museum, behind glass that has protected it for centuries, 
        lies the Alfred Jewel—a masterpiece of Anglo-Saxon craftsmanship. Barely 
        larger than a thumb, this golden artifact bears the inscription "AELFRED MEC 
        HEHT GEWYRCAN"—Alfred ordered me to be made.
        
        King Alfred the Great commissioned this jewel over a thousand years ago, perhaps 
        as a pointer for reading sacred texts. The enamel figure gazes out with knowing 
        eyes, holding flowering rods, forever frozen in a moment of medieval artistry. 
        Gold, enamel, and rock crystal—materials that would outlast kingdoms.
        
        Discovered in 1693 in a Somerset field, the jewel had waited centuries in the 
        earth. What stories could it tell? Of the king who held it, of the craftsman 
        who shaped it, of the battles and books and prayers it witnessed. In your 
        reflection in its glass case, you become part of its endless story—another 
        pair of eyes that has beheld its beauty, another moment in its long existence.
    """,
    "story2": """
        The Oxford Dodo stands in the Museum of Natural History, the most famous 
        extinct bird in the world. Unlike the complete skeletons elsewhere, this is 
        something more poignant—the only soft tissue remains of a dodo anywhere. 
        A head and a foot, dried and preserved, the last physical remnants of a 
        species that vanished from Earth in the 1660s.
        
        These fragments once belonged to the Tradescant collection, displayed as a 
        curiosity when dodos still lived on Mauritius. The museum's founder almost 
        had the deteriorating specimen destroyed, but an assistant saved the head and 
        foot—the only reason we can see real dodo tissue today. Every other dodo is 
        bones, or paintings, or descriptions.
        
        Standing before this display, you're looking at absence made visible. The dodo 
        became extinct before science understood extinction was possible. This bird's 
        remnants ask a question that echoes across centuries: What are we losing now 
        that we don't yet realize we should save? The dodo watches with its preserved 
        eye, a witness to its own species' ending, a warning written in feathers and bone.
    """,
    "story3": """
        In the Ashmolean Museum rests an unassuming lantern—metal, practical, 
        unremarkable except for one detail: it was carried by Guy Fawkes on the night 
        of November 5th, 1605, when he was discovered in the cellars beneath Parliament, 
        guarding thirty-six barrels of gunpowder.
        
        Imagine the flickering flame inside this lantern, casting shadows on stone walls, 
        illuminating the face of a man who believed he was about to change history with 
        fire. The Gunpowder Plot failed, of course. Fawkes was arrested, tortured, and 
        executed. But his lantern survived.
        
        For over four hundred years, this simple light-bearer has endured. It witnessed 
        the night when England's entire government nearly vanished in an explosion. It 
        was there in the darkness of conspiracy, in the moment of discovery, in the 
        instant when rebellion became capture. Every November 5th, when bonfires light 
        the British sky, this lantern sits quiet in its case—the authentic flame that 
        nearly ignited revolution, now cold, now still, now only light in memory.
    """,
    "story4": """
        The Scorpion Macehead sits among Egyptian treasures in the Ashmolean, carved 
        from limestone over 5,000 years ago. It depicts a king—possibly named Scorpion, 
        or perhaps the scorpion is merely a symbol—performing a ceremonial act: cutting 
        an irrigation canal, bringing water and life to the land.
        
        This was made before the pyramids, before hieroglyphic writing was fully 
        developed, in an Egypt that was still becoming Egypt. The carving shows 
        attendants, standards, birds—a snapshot of a world that existed fifty centuries 
        before Instagram, yet the artist's skill still speaks clearly across that 
        impossible gulf of time.
        
        Look closely at the scorpion symbol above the king's head. Scholars debate who 
        this ruler was, whether he united Upper Egypt, whether he was the same king 
        depicted on the Narmer Palette. But the mystery makes it more powerful. This 
        stone has outlasted certainty itself. Empires rose and fell, languages were 
        born and died, and still this macehead endures—a king without a name, a story 
        without an ending, a moment carved in stone when the world was young.
    """,
    "story5": """
        Hanging in the Ashmolean is a deerskin mantle embroidered with shells, forming 
        patterns of a human figure flanked by animals. This is Powhatan's Mantle—or 
        rather, it might be. The cloak belonged to the Powhatan people of Virginia, 
        possibly to Chief Powhatan himself, father of Pocahontas, who met the Jamestown 
        colonists in 1607.
        
        The shells tell a story in their arrangement—a cosmology, a map of power, a 
        world-view sewn into hide. Each shell was carefully selected, pierced, and 
        attached. The labor represents not just hours but meaning, not just craft but 
        culture. This was wealth and authority made visible, made wearable.
        
        The mantle arrived in England in the 1630s, part of John Tradescant's collection 
        of "rarities and curiosities." But it's not a curiosity—it's a voice. In an era 
        when Indigenous peoples were being pushed from their lands, this mantle survived, 
        carrying its maker's vision across the ocean, across centuries. Stand before it 
        and you're not looking at an artifact. You're receiving a message from a world 
        that refused to be forgotten, embroidered with shells that shine like stars, 
        telling stories that shine like truth.
    """,
    "story6": """
        The Abingdon Sword lies in its case, pattern-welded steel from the seventh 
        century, discovered in a Saxon cemetery. The blade shows the technique of 
        combining iron and steel, twisted and forged, creating both strength and beauty—
        the swirling patterns visible even now, like water frozen in metal.
        
        This sword was made for a warrior of status, buried with them for the journey 
        beyond death. The Anglo-Saxon world believed a good sword had a spirit, a 
        personality. Beowulf spoke of swords by name. This blade likely had a name too, 
        now lost to time, whispered by voices speaking a language that evolved into 
        English but would sound alien to modern ears.
        
        The sword rested in the earth for thirteen centuries, returning to the darkness 
        from which its metal was first drawn. When archaeologists uncovered it, they 
        found corrosion and soil, but beneath—still there—the pattern welding, the 
        careful craftsmanship, the respect for the warrior it accompanied. Every sword 
        tells two stories: the life of the one who wielded it, and the skill of the 
        one who forged it. Both stories are here, waiting in the steel.
    """,
    "story7": """
        The Ashmolean Museum began with John Tradescant's "Ark"—a cabinet of curiosities 
        assembled in the 1600s, perhaps the first museum collection in England. Tradescant 
        traveled the world bringing back wonders: a dodo, a volcanic rock from Vesuvius, 
        a flying squirrel, Guy Fawkes' lantern, Powhatan's mantle, coins, shells, and 
        countless "rarities" that amazed visitors.
        
        In Tradescant's garden in Lambeth, you could see the first pineapple grown in 
        England, plants from Virginia, flowers from the Mediterranean. His collection 
        was called "The Ark" because, like Noah's vessel, it preserved specimens of 
        Earth's diversity. It was science and spectacle combined, an attempt to gather 
        the whole world under one roof.
        
        When Elias Ashmole inherited and donated the collection to Oxford in 1683, the 
        Ashmolean Museum was born—the world's first university museum. Tradescant's 
        curiosity became institution, his personal ark became public treasure. Today, 
        millions walk through galleries that exist because one man couldn't stop asking 
        "What else is out there?" The Ark has landed, but the voyage of discovery 
        continues—every object a port of call, every display case a window to another 
        world.
    """,
    "story8": """
        The Parian Marble, also called the Marmor Parium, is a chronological table carved 
        in Greek on a marble slab around 264 BCE. It lists dates and events from Greek 
        mythology and history, beginning with the reign of Cecrops, the first king of 
        Athens (1581 BCE by its reckoning), down to 264 BCE when it was carved.
        
        This isn't just history—it's how ancient Greeks understood their own past. The 
        marble treats myths and historical events with equal seriousness: the flood of 
        Deucalion, the founding of the Eleusinian Mysteries, the first Olympiad, the 
        birth of Homer. To the Greeks, these weren't separate categories. The past was 
        continuous, divine and human events intertwined.
        
        Discovered on the island of Paros in the 1600s, this fragment came to Oxford 
        where generations of scholars have puzzled over its dates and entries. It's a 
        ghost of an ancient library, a bookmark in a civilization's memory. When you 
        read these carved lines, you're seeing the past through Greek eyes, standing 
        in their timeline, measuring history by their markers. The marble endures, 
        still counting, still remembering, a clock that stopped ticking but never 
        stopped telling time.
    """,
    "story9": """
        In the Pitt Rivers Museum, dim lighting reveals rows of ceremonial axes—jade, 
        stone, greenstone—from cultures across the Pacific. These weren't tools for 
        chopping wood. These were power made tangible, authority carved into stone, 
        connections between earth and ancestors given physical form.
        
        The Maori mere, the jade clubs of chiefs, were taonga—treasures with their own 
        mana, their own spiritual essence. They were named, their lineages remembered, 
        passed down through generations. To hold such an axe was to hold the strength 
        of those who held it before, to touch a chain of hands stretching back to the 
        time when the stone was first shaped.
        
        Lieutenant-General Pitt Rivers collected these objects believing they showed 
        the "evolution" of human culture. He was wrong about that—these aren't primitive 
        versions of European tools but sophisticated expressions of different worldviews. 
        Yet his collection preserves something valuable: the diversity of human imagination, 
        the thousand different ways people have carved meaning into stone. Each axe is a 
        philosophy made solid. Each blade reflects a different answer to the question: 
        What is sacred? What is worth making beautiful? What should last?
    """,
    "story10": """
        In the Museum of the History of Science hangs a blackboard—just a blackboard, 
        marked with chalk equations, seemingly ordinary. Except these equations were 
        written by Albert Einstein during a lecture at Oxford on May 16, 1931, exploring 
        his evolving theories about the expanding universe.
        
        The board was never erased. Someone recognized that history was written there 
        in chalk dust, that those symbols represented a mind grappling with the nature 
        of reality itself. Einstein was still refining his ideas about cosmology, still 
        arguing with the evidence that the universe was expanding—something he'd initially 
        resisted with his cosmological constant.
        
        The chalk is fading now, the equations growing faint. But they remain visible: 
        mathematics as thought made visible, genius captured mid-lecture, the moment when 
        Einstein shared his vision of curved spacetime with a room of Oxford scholars. 
        The blackboard is a window into the process of discovery—not polished theory from 
        textbooks, but working ideas, hypotheses in progress, the actual chalk-marks of 
        someone trying to understand the universe. Stand before it and you're attending 
        that 1931 lecture, watching Einstein think, seeing the moment when human consciousness 
        reached for the stars and wrote equations to explain their dance.
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
    
    # Redirect to completion page with options
    return redirect(url_for('story_completed', story_id=story_id))

@app.route('/story_completed/<story_id>')
def story_completed(story_id):
    """Show post-reading options (mood and like)"""
    story = recommender.stories.get(story_id)
    if not story:
        return redirect(url_for('index'))
    
    user_id = get_user_id()
    user = recommender.users.get(user_id)
    mood_before = user.current_mood.value if user and user.current_mood else None
    
    # Check if already liked
    already_liked = user and story_id in user.favorited_stories
    
    return render_template('story_completed.html', 
                         story=story, 
                         mood_before=mood_before,
                         already_liked=already_liked)

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
    
    # Check where to redirect
    next_page = request.form.get('next', 'recommendations')
    if next_page == 'story_completed':
        return redirect(url_for('story_completed', story_id=story_id))
    return redirect(url_for('recommendations'))

@app.route('/like_story/<story_id>', methods=['POST'])
def like_story(story_id):
    """Like a story (same as favorite)"""
    user_id = get_user_id()
    
    event = AnalyticsEvent(
        user_id,
        'favorite',
        datetime.now(),
        story_id=story_id
    )
    recommender.add_event(event)
    
    # Redirect back to where the user came from
    return redirect(request.referrer or url_for('recommendations'))

@app.route('/favorite/<story_id>', methods=['POST'])
def favorite_story(story_id):
    """Add story to favorites (legacy route, redirects to like_story)"""
    return like_story(story_id)

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
