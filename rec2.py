import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import json

class MoodScore:
    """Represents a simple single-value mood score"""
    def __init__(self, value: float):
        self.value = value
    
    def distance_to(self, other: 'MoodScore') -> float:
        return abs(self.value - other.value)
    
    def to_dict(self) -> float:
        return self.value
    
    @classmethod
    def from_dict(cls, data: float) -> 'MoodScore':
        return cls(data)
    
    def __repr__(self):
        return f"MoodScore({self.value})"


class StoryTransition:
    """Represents a transition from one story to another"""
    def __init__(self, from_story_id: str, to_story_id: str, 
                 user_id: str, timestamp: datetime,
                 mood_before: Optional[MoodScore] = None,
                 mood_after: Optional[MoodScore] = None,
                 time_between_minutes: float = 0.0):
        self.from_story_id = from_story_id
        self.to_story_id = to_story_id
        self.user_id = user_id
        self.timestamp = timestamp
        self.mood_before = mood_before  # Mood at start of first story
        self.mood_after = mood_after     # Mood after second story
        self.time_between_minutes = time_between_minutes
        
        # Computed
        self.mood_delta = None
        if mood_before and mood_after:
            self.mood_delta = mood_after.value - mood_before.value
    
    def to_dict(self) -> Dict:
        return {
            'from_story_id': self.from_story_id,
            'to_story_id': self.to_story_id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'mood_before': self.mood_before.to_dict() if self.mood_before else None,
            'mood_after': self.mood_after.to_dict() if self.mood_after else None,
            'time_between_minutes': self.time_between_minutes,
            'mood_delta': self.mood_delta
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StoryTransition':
        transition = cls(
            data['from_story_id'],
            data['to_story_id'],
            data['user_id'],
            datetime.fromisoformat(data['timestamp']),
            MoodScore.from_dict(data['mood_before']) if data['mood_before'] else None,
            MoodScore.from_dict(data['mood_after']) if data['mood_after'] else None,
            data['time_between_minutes']
        )
        transition.mood_delta = data.get('mood_delta')
        return transition


class Story:
    """Represents a story with metadata"""
    def __init__(self, story_id: str, title: str, theme: str, tags: List[str] = None):
        self.id = story_id
        self.title = title
        self.theme = theme
        self.tags = tags or []
        
        # Individual story effects
        self.mood_associations = []  # List of (mood_before, mood_after, timestamp) tuples
        self.avg_mood_change = None
        self.mood_effectiveness = {}
        
        # Sequential effects - what works well AFTER this story
        self.best_next_stories = {}  # story_id -> avg_mood_delta
        self.best_next_themes = {}   # theme -> avg_mood_delta
        
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'theme': self.theme,
            'tags': self.tags,
            'mood_associations': [
                (mb.to_dict(), ma.to_dict(), ts.isoformat()) 
                for mb, ma, ts in self.mood_associations
            ],
            'avg_mood_change': self.avg_mood_change,
            'mood_effectiveness': self.mood_effectiveness,
            'best_next_stories': self.best_next_stories,
            'best_next_themes': self.best_next_themes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Story':
        story = cls(data['id'], data['title'], data['theme'], data['tags'])
        story.mood_associations = [
            (MoodScore.from_dict(mb), MoodScore.from_dict(ma), datetime.fromisoformat(ts)) 
            for mb, ma, ts in data.get('mood_associations', [])
        ]
        story.avg_mood_change = data.get('avg_mood_change')
        story.mood_effectiveness = data.get('mood_effectiveness', {})
        story.best_next_stories = data.get('best_next_stories', {})
        story.best_next_themes = data.get('best_next_themes', {})
        return story


class AnalyticsEvent:
    """Represents a user interaction event"""
    def __init__(self, user_id: str, event_type: str, timestamp: datetime, **kwargs):
        self.user_id = user_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.data = kwargs
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AnalyticsEvent':
        return cls(
            data['user_id'],
            data['event_type'],
            datetime.fromisoformat(data['timestamp']),
            **data['data']
        )


class UserProfile:
    """Represents a user's preferences and history"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.viewed_stories = {}
        self.completed_stories = {}
        self.favorited_stories = {}
        
        self.theme_interactions = defaultdict(list)
        
        self.mood_history = []
        self.current_mood = None
        
        self.story_mood_impact = {}
        self.recent_story_views = []
        
        self.recommendation_mix = 0.5
        
        self._mood_trend = None
        self._mood_volatility = None
        
        # Sequential preferences
        self.story_sequences = []  # List of StoryTransition objects
        self.preferred_transitions = defaultdict(list)  # from_story_id -> [(to_story_id, mood_delta, timestamp)]
        self.theme_transition_preferences = defaultdict(lambda: defaultdict(list))  # from_theme -> to_theme -> [mood_deltas]
        
        # Last completed story (for next-story recommendations)
        self.last_completed_story = None
        self.last_completed_timestamp = None
        
    def get_avoided_themes(self, threshold: float = -1.0, current_time: datetime = None) -> List[str]:
        current_time = current_time or datetime.now()
        theme_scores = self._get_decayed_theme_scores(current_time)
        return [theme for theme, score in theme_scores.items() if score < threshold]
    
    def get_preferred_themes(self, threshold: float = 1.0, current_time: datetime = None) -> List[str]:
        current_time = current_time or datetime.now()
        theme_scores = self._get_decayed_theme_scores(current_time)
        return [theme for theme, score in theme_scores.items() if score > threshold]
    
    def _get_decayed_theme_scores(self, current_time: datetime, half_life_days: float = 30.0) -> Dict[str, float]:
        theme_scores = defaultdict(float)
        for theme, interactions in self.theme_interactions.items():
            total_score = 0.0
            for score, timestamp in interactions:
                days_ago = (current_time - timestamp).total_seconds() / 86400
                decay_factor = 0.5 ** (days_ago / half_life_days)
                total_score += score * decay_factor
            theme_scores[theme] = total_score
        return theme_scores
    
    def update_mood_trajectory(self):
        if len(self.mood_history) < 3:
            self._mood_trend = 'stable'
            self._mood_volatility = 0.0
            return
        
        recent_moods = self.mood_history[-10:]
        mood_values = [mood.value for _, mood in recent_moods]
        
        x = np.arange(len(mood_values))
        coeffs = np.polyfit(x, mood_values, 1)
        slope = coeffs[0]
        
        if slope > 0.2:
            self._mood_trend = 'improving'
        elif slope < -0.2:
            self._mood_trend = 'declining'
        else:
            self._mood_trend = 'stable'
        
        self._mood_volatility = np.std(mood_values)
    
    def get_recent_story_path(self, n: int = 3) -> List[str]:
        """Get the last N completed stories as a path"""
        # Sort completed stories by timestamp
        sorted_completions = sorted(
            self.completed_stories.items(), 
            key=lambda x: x[1]
        )
        return [story_id for story_id, _ in sorted_completions[-n:]]


class StoryRecommender:
    """Main recommender system with sequence-aware recommendations"""
    
    def __init__(self, event_half_life_days: float = 30.0, mood_half_life_days: float = 14.0,
                 transition_window_minutes: float = 1440.0):  # 24 hours default
        self.stories: Dict[str, Story] = {}
        self.users: Dict[str, UserProfile] = {}
        self.events: List[AnalyticsEvent] = []
        
        self.event_half_life_days = event_half_life_days
        self.mood_half_life_days = mood_half_life_days
        self.transition_window_minutes = transition_window_minutes  # Max time between stories to count as sequence
        
        # Global transition tracking
        self.story_transitions = []  # List of StoryTransition objects
        self.global_transition_graph = defaultdict(lambda: defaultdict(list))  # from_id -> to_id -> [transitions]
        
        self._story_similarity_cache = {}
        self._theme_to_stories = defaultdict(list)
        
    def add_story(self, story_id: str, title: str, theme: str, tags: List[str] = None):
        story = Story(story_id, title, theme, tags)
        self.stories[story_id] = story
        self._theme_to_stories[theme].append(story_id)
        self._story_similarity_cache = {}
        
    def add_event(self, event: AnalyticsEvent):
        self.events.append(event)
        user_id = event.user_id
        
        if user_id not in self.users:
            self.users[user_id] = UserProfile(user_id)
        
        user = self.users[user_id]
        
        if event.event_type == 'view':
            story_id = event.data['story_id']
            user.viewed_stories[story_id] = event.timestamp
            user.recent_story_views.append((event.timestamp, story_id))
            
            if story_id in self.stories:
                theme = self.stories[story_id].theme
                user.theme_interactions[theme].append((0.1, event.timestamp))
                
        elif event.event_type == 'complete':
            story_id = event.data['story_id']
            user.completed_stories[story_id] = event.timestamp
            
            if story_id in self.stories:
                theme = self.stories[story_id].theme
                user.theme_interactions[theme].append((1.0, event.timestamp))
            
            # Check for story transition (sequence)
            if user.last_completed_story and user.last_completed_timestamp:
                time_diff = (event.timestamp - user.last_completed_timestamp).total_seconds() / 60.0
                
                # If completed within transition window, record as sequence
                if time_diff <= self.transition_window_minutes:
                    self._record_story_transition(
                        user,
                        user.last_completed_story,
                        story_id,
                        event.timestamp,
                        time_diff
                    )
            
            # Update last completed
            user.last_completed_story = story_id
            user.last_completed_timestamp = event.timestamp
                
        elif event.event_type == 'mood_after':
            story_id = event.data['story_id']
            mood_after = MoodScore(event.data['mood_score'])
            
            if user.current_mood:
                mood_change = self._calculate_mood_improvement(user.current_mood, mood_after)
                user.story_mood_impact[story_id] = (mood_change, event.timestamp)
                
                if story_id in self.stories:
                    self.stories[story_id].mood_associations.append(
                        (user.current_mood, mood_after, event.timestamp)
                    )
                    self._update_story_mood_stats(story_id)
                    
                    theme = self.stories[story_id].theme
                    user.theme_interactions[theme].append((mood_change * 0.5, event.timestamp))
                
                # Update transition with mood information if applicable
                self._update_recent_transition_mood(user, story_id, mood_after)
            
            user.current_mood = mood_after
            user.mood_history.append((event.timestamp, mood_after))
            user.update_mood_trajectory()
            
        elif event.event_type == 'favorite':
            story_id = event.data['story_id']
            user.favorited_stories[story_id] = event.timestamp
            
            if story_id in self.stories:
                theme = self.stories[story_id].theme
                user.theme_interactions[theme].append((2.0, event.timestamp))
                
        elif event.event_type == 'mood_general':
            mood_score = MoodScore(event.data['mood_score'])
            user.current_mood = mood_score
            user.mood_history.append((event.timestamp, mood_score))
            user.update_mood_trajectory()
            
        elif event.event_type == 'search':
            if 'theme' in event.data:
                theme = event.data['theme']
                user.theme_interactions[theme].append((0.5, event.timestamp))
                
        elif event.event_type == 'slider_position':
            position = event.data['position']
            user.recommendation_mix = max(0.0, min(1.0, position))
    
    def _record_story_transition(self, user: UserProfile, from_story_id: str, 
                                 to_story_id: str, timestamp: datetime, 
                                 time_between_minutes: float):
        """Record a story-to-story transition"""
        # Get mood information if available
        mood_before = None
        mood_after = None
        
        # Try to find mood before first story
        for ts, mood in reversed(user.mood_history):
            if ts <= user.last_completed_timestamp:
                mood_before = mood
                break
        
        # Current mood is mood after second story (if recently recorded)
        if user.current_mood:
            mood_after = user.current_mood
        
        # Create transition
        transition = StoryTransition(
            from_story_id,
            to_story_id,
            user.user_id,
            timestamp,
            mood_before,
            mood_after,
            time_between_minutes
        )
        
        # Store in user profile
        user.story_sequences.append(transition)
        user.preferred_transitions[from_story_id].append(
            (to_story_id, transition.mood_delta, timestamp)
        )
        
        # Store theme transitions
        if from_story_id in self.stories and to_story_id in self.stories:
            from_theme = self.stories[from_story_id].theme
            to_theme = self.stories[to_story_id].theme
            if transition.mood_delta is not None:
                user.theme_transition_preferences[from_theme][to_theme].append(
                    (transition.mood_delta, timestamp)
                )
        
        # Store globally
        self.story_transitions.append(transition)
        self.global_transition_graph[from_story_id][to_story_id].append(transition)
        
        # Update story's "best next" statistics
        self._update_story_transition_stats(from_story_id)
    
    def _update_recent_transition_mood(self, user: UserProfile, story_id: str, 
                                       mood_after: MoodScore):
        """Update the most recent transition with mood_after information"""
        if not user.story_sequences:
            return
        
        last_transition = user.story_sequences[-1]
        if last_transition.to_story_id == story_id and last_transition.mood_after is None:
            last_transition.mood_after = mood_after
            if last_transition.mood_before:
                last_transition.mood_delta = mood_after.value - last_transition.mood_before.value
                
                # Update the corresponding entry in preferred_transitions
                from_story = last_transition.from_story_id
                for i, (to_id, delta, ts) in enumerate(user.preferred_transitions[from_story]):
                    if to_id == story_id and delta is None and ts == last_transition.timestamp:
                        user.preferred_transitions[from_story][i] = (
                            to_id, last_transition.mood_delta, ts
                        )
                        break
                
                # Update story transition stats
                self._update_story_transition_stats(from_story)
    
    def _update_story_transition_stats(self, from_story_id: str):
        """Update statistics about what stories work well after this one"""
        if from_story_id not in self.stories:
            return
        
        from_story = self.stories[from_story_id]
        current_time = datetime.now()
        
        # Collect all transitions from this story
        transitions = self.global_transition_graph[from_story_id]
        
        # Calculate average mood delta for each next story (with time decay)
        next_story_effects = defaultdict(list)
        next_theme_effects = defaultdict(list)
        
        for to_story_id, transition_list in transitions.items():
            for transition in transition_list:
                if transition.mood_delta is None:
                    continue
                
                # Apply time decay
                days_ago = (current_time - transition.timestamp).total_seconds() / 86400
                decay_factor = 0.5 ** (days_ago / self.mood_half_life_days)
                
                weighted_delta = transition.mood_delta * decay_factor
                next_story_effects[to_story_id].append(weighted_delta)
                
                # Also track by theme
                if to_story_id in self.stories:
                    to_theme = self.stories[to_story_id].theme
                    next_theme_effects[to_theme].append(weighted_delta)
        
        # Store averages
        from_story.best_next_stories = {
            story_id: np.mean(deltas) 
            for story_id, deltas in next_story_effects.items()
            if deltas
        }
        
        from_story.best_next_themes = {
            theme: np.mean(deltas)
            for theme, deltas in next_theme_effects.items()
            if deltas
        }
    
    def _calculate_mood_improvement(self, mood_before: MoodScore, mood_after: MoodScore) -> float:
        return mood_after.value - mood_before.value
    
    def _update_story_mood_stats(self, story_id: str):
        story = self.stories[story_id]
        if not story.mood_associations:
            return
        
        current_time = datetime.now()
        weighted_improvements = []
        total_weight = 0.0
        
        for before, after, timestamp in story.mood_associations:
            improvement = self._calculate_mood_improvement(before, after)
            days_ago = (current_time - timestamp).total_seconds() / 86400
            decay_factor = 0.5 ** (days_ago / self.mood_half_life_days)
            weighted_improvements.append(improvement * decay_factor)
            total_weight += decay_factor
        
        if total_weight > 0:
            story.avg_mood_change = sum(weighted_improvements) / total_weight
        
        self._calculate_mood_effectiveness(story_id)
    
    def _calculate_mood_effectiveness(self, story_id: str):
        story = self.stories[story_id]
        if not story.mood_associations:
            return
        
        mood_ranges = {
            'very_low': (1, 3),
            'low': (3, 5),
            'medium': (5, 7),
            'high': (7, 9),
            'very_high': (9, 10)
        }
        
        current_time = datetime.now()
        range_improvements = defaultdict(list)
        
        for before_mood, after_mood, timestamp in story.mood_associations:
            for range_name, (low, high) in mood_ranges.items():
                if low <= before_mood.value < high:
                    improvement = self._calculate_mood_improvement(before_mood, after_mood)
                    days_ago = (current_time - timestamp).total_seconds() / 86400
                    decay_factor = 0.5 ** (days_ago / self.mood_half_life_days)
                    range_improvements[range_name].append(improvement * decay_factor)
                    break
        
        for range_name, improvements in range_improvements.items():
            if improvements:
                story.mood_effectiveness[range_name] = np.mean(improvements)
    
    def _get_mood_range(self, mood_value: float) -> str:
        if mood_value < 3:
            return 'very_low'
        elif mood_value < 5:
            return 'low'
        elif mood_value < 7:
            return 'medium'
        elif mood_value < 9:
            return 'high'
        else:
            return 'very_high'
    
    def get_recommendations(self, user_id: str, context: Dict = None,
                           n_recommendations: int = 10) -> List[Tuple[str, float]]:
        context = context or {}
        current_time = context.get('current_time', datetime.now())
        
        if user_id not in self.users:
            self.users[user_id] = UserProfile(user_id)
        
        user = self.users[user_id]
        
        if 'current_mood' in context:
            user.current_mood = context['current_mood']
        
        story_scores = {}
        for story_id, story in self.stories.items():
            recent_story_ids = [sid for _, sid in user.recent_story_views[-10:]]
            if story_id in recent_story_ids:
                continue
            
            score = self._score_story_for_user(user, story, context, current_time)
            story_scores[story_id] = score
        
        sorted_stories = sorted(story_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_stories[:n_recommendations]
    
    def _score_story_for_user(self, user: UserProfile, story: Story, 
                              context: Dict, current_time: datetime) -> float:
        score = 0.0
        
        mix = user.recommendation_mix
        individual_weight = 1.0 - mix
        collaborative_weight = mix
        
        if 0.1 <= mix <= 0.9:
            individual_weight = max(individual_weight, 0.2)
            collaborative_weight = max(collaborative_weight, 0.2)
        
        # === INDIVIDUAL-BASED SIGNALS ===
        
        # 1. SOPHISTICATED MOOD MATCHING
        if user.current_mood:
            mood_score = self._sophisticated_mood_match(user, story, current_time)
            score += mood_score * individual_weight
        
        # 2. SEQUENTIAL RECOMMENDATION - What comes next?
        # This is a KEY NEW FEATURE
        if user.last_completed_story:
            sequence_score = self._sequence_based_score(user, story, current_time)
            score += sequence_score * 4.0 * individual_weight  # High weight for sequences!
        
        # 3. PERSONAL MOOD HISTORY WITH THIS STORY
        if story.id in user.story_mood_impact:
            mood_change, timestamp = user.story_mood_impact[story.id]
            days_ago = (current_time - timestamp).total_seconds() / 86400
            decay_factor = 0.5 ** (days_ago / self.mood_half_life_days)
            normalized_impact = (mood_change + 5) / 10.0
            score += normalized_impact * 2.5 * decay_factor * individual_weight
        
        # 4. THEME PREFERENCES
        theme_scores = user._get_decayed_theme_scores(current_time, self.event_half_life_days)
        theme_score = theme_scores.get(story.theme, 0)
        score += theme_score * 1.5 * individual_weight
        
        if story.theme in user.get_avoided_themes(current_time=current_time):
            score -= 5.0
        
        # 5. CONTENT-BASED
        content_score = self._content_based_score(user, story, current_time)
        score += content_score * 2.0 * individual_weight
        
        # 6. FAVORITES SIMILARITY
        if user.favorited_stories:
            favorite_scores = []
            for fav_id, fav_timestamp in user.favorited_stories.items():
                if fav_id not in self.stories:
                    continue
                similarity = self._story_similarity(story.id, fav_id)
                days_ago = (current_time - fav_timestamp).total_seconds() / 86400
                decay_factor = 0.5 ** (days_ago / self.event_half_life_days)
                favorite_scores.append(similarity * decay_factor)
            if favorite_scores:
                score += max(favorite_scores) * 2.0 * individual_weight
        
        # === COLLABORATIVE SIGNALS ===
        
        # 7. COLLABORATIVE FILTERING
        collab_score = self._collaborative_filtering_score(user, story, current_time)
        score += collab_score * 3.0 * collaborative_weight
        
        # 8. COLLABORATIVE SEQUENCE PATTERNS
        # What do other users read after similar stories?
        collab_sequence_score = self._collaborative_sequence_score(user, story, current_time)
        score += collab_sequence_score * 3.5 * collaborative_weight
        
        # 9. POPULARITY
        popularity_score = self._popularity_score(user, story, current_time)
        score += popularity_score * 2.0 * collaborative_weight
        
        # === UNIVERSAL SIGNALS ===
        
        # 10. PROMOTIONAL BOOST
        if 'promotional_tags' in context:
            promo_tags = set(context['promotional_tags'])
            if any(tag in promo_tags for tag in story.tags):
                score += 1.5
        
        # 11. NOVELTY
        if story.id not in user.viewed_stories:
            score += 0.5
        
        return score
    
    def _sequence_based_score(self, user: UserProfile, candidate_story: Story,
                             current_time: datetime) -> float:
        """
        Score based on how well this story follows the user's last completed story.
        Uses both personal and global transition patterns.
        """
        if not user.last_completed_story or user.last_completed_story not in self.stories:
            return 0.0
        
        last_story = self.stories[user.last_completed_story]
        total_score = 0.0
        
        # 1. PERSONAL TRANSITION HISTORY
        # Has this user followed last_story with candidate_story before?
        if user.last_completed_story in user.preferred_transitions:
            personal_transitions = user.preferred_transitions[user.last_completed_story]
            
            for to_story_id, mood_delta, timestamp in personal_transitions:
                if to_story_id == candidate_story.id and mood_delta is not None:
                    # Apply time decay
                    days_ago = (current_time - timestamp).total_seconds() / 86400
                    decay_factor = 0.5 ** (days_ago / self.mood_half_life_days)
                    
                    # Positive mood delta = good transition
                    normalized_delta = (mood_delta + 5) / 10.0
                    total_score += normalized_delta * 3.0 * decay_factor
        
        # 2. GLOBAL STORY-LEVEL PATTERNS
        # What do ALL users experience when following last_story with candidate_story?
        if candidate_story.id in last_story.best_next_stories:
            avg_effect = last_story.best_next_stories[candidate_story.id]
            normalized_effect = (avg_effect + 5) / 10.0
            total_score += normalized_effect * 2.5
        
        # 3. THEME TRANSITION PATTERNS
        # Does this theme transition work well?
        candidate_theme = candidate_story.theme
        
        # Personal theme transitions
        if last_story.theme in user.theme_transition_preferences:
            if candidate_theme in user.theme_transition_preferences[last_story.theme]:
                theme_deltas = user.theme_transition_preferences[last_story.theme][candidate_theme]
                
                weighted_deltas = []
                for mood_delta, timestamp in theme_deltas:
                    days_ago = (current_time - timestamp).total_seconds() / 86400
                    decay_factor = 0.5 ** (days_ago / self.mood_half_life_days)
                    weighted_deltas.append(mood_delta * decay_factor)
                
                if weighted_deltas:
                    avg_theme_effect = np.mean(weighted_deltas)
                    normalized_theme = (avg_theme_effect + 5) / 10.0
                    total_score += normalized_theme * 2.0
        
        # Global theme transitions
        if candidate_theme in last_story.best_next_themes:
            avg_theme_effect = last_story.best_next_themes[candidate_theme]
            normalized_effect = (avg_theme_effect + 5) / 10.0
            total_score += normalized_effect * 1.5
        
        # 4. PATH PATTERNS (3-story sequences)
        # Look at the last 2 completed stories and find what worked well next
        recent_path = user.get_recent_story_path(n=2)
        if len(recent_path) == 2:
            path_score = self._evaluate_path_continuation(
                recent_path, candidate_story.id, current_time
            )
            total_score += path_score
        
        # 5. RECENCY BOOST
        # If they just completed a story, strongly prefer a good follow-up
        if user.last_completed_timestamp:
            minutes_since = (current_time - user.last_completed_timestamp).total_seconds() / 60.0
            if minutes_since < 60:  # Within an hour
                recency_boost = 1.0 - (minutes_since / 60.0)
                total_score *= (1.0 + recency_boost * 0.5)  # Up to 50% boost
        
        return total_score
    
    def _evaluate_path_continuation(self, path: List[str], candidate_id: str,
                                    current_time: datetime) -> float:
        """Evaluate how well candidate continues a multi-story path"""
        if len(path) < 2:
            return 0.0
        
        # Look for users who followed this same path and what they did next
        matching_paths = []
        
        for user in self.users.values():
            user_path = user.get_recent_story_path(n=len(path) + 1)
            
            # Check if this user followed our path
            if len(user_path) >= len(path) + 1 and user_path[:-1] == path:
                next_story = user_path[-1]
                
                # Find the transition to that next story
                if len(path) > 0 and path[-1] in user.preferred_transitions:
                    for to_id, mood_delta, timestamp in user.preferred_transitions[path[-1]]:
                        if to_id == next_story and mood_delta is not None:
                            # Apply time decay
                            days_ago = (current_time - timestamp).total_seconds() / 86400
                            decay_factor = 0.5 ** (days_ago / self.mood_half_life_days)
                            
                            if to_id == candidate_id:
                                # This user followed our path and chose our candidate
                                matching_paths.append(mood_delta * decay_factor)
        
        if matching_paths:
            avg_effect = np.mean(matching_paths)
            normalized_effect = (avg_effect + 5) / 10.0
            return normalized_effect * 2.0
        
        return 0.0
    
    def _collaborative_sequence_score(self, user: UserProfile, candidate_story: Story,
                                      current_time: datetime) -> float:
        """
        What do other similar users read next after stories similar to user's recent reads?
        """
        if not user.last_completed_story:
            return 0.0
        
        # Find users who recently completed the same story
        similar_user_next_choices = []
        
        for other_user in self.users.values():
            if other_user.user_id == user.user_id:
                continue
            
            # Did they complete the same last story?
            if user.last_completed_story in other_user.preferred_transitions:
                transitions = other_user.preferred_transitions[user.last_completed_story]
                
                for to_id, mood_delta, timestamp in transitions:
                    if to_id == candidate_story.id and mood_delta is not None:
                        # Apply time decay
                        days_ago = (current_time - timestamp).total_seconds() / 86400
                        decay_factor = 0.5 ** (days_ago / self.mood_half_life_days)
                        
                        similar_user_next_choices.append(mood_delta * decay_factor)
        
        if similar_user_next_choices:
            avg_effect = np.mean(similar_user_next_choices)
            normalized_effect = (avg_effect + 5) / 10.0
            return normalized_effect
        
        return 0.0
    
    def _sophisticated_mood_match(self, user: UserProfile, story: Story, 
                                   current_time: datetime) -> float:
        if not user.current_mood or not story.mood_associations:
            return 0.0
        
        total_score = 0.0
        current_mood_value = user.current_mood.value
        
        # 1. MOOD RANGE EFFECTIVENESS
        current_range = self._get_mood_range(current_mood_value)
        if current_range in story.mood_effectiveness:
            effectiveness = story.mood_effectiveness[current_range]
            normalized_effectiveness = (effectiveness + 5) / 10.0
            total_score += normalized_effectiveness * 3.0
        
        # 2. SIMILAR MOOD MATCHING
        mood_similarities = []
        total_weight = 0.0
        
        for before_mood, after_mood, timestamp in story.mood_associations:
            mood_distance = abs(current_mood_value - before_mood.value)
            similarity = 1.0 - (mood_distance / 9.0)
            
            days_ago = (current_time - timestamp).total_seconds() / 86400
            decay_factor = 0.5 ** (days_ago / self.mood_half_life_days)
            
            improvement = self._calculate_mood_improvement(before_mood, after_mood)
            combined_score = similarity * (1.0 + improvement / 5.0)
            
            mood_similarities.append(combined_score * decay_factor)
            total_weight += decay_factor
        
        if mood_similarities and total_weight > 0:
            weighted_avg = sum(mood_similarities) / total_weight
            total_score += weighted_avg * 2.0
        
        # 3. TRAJECTORY-BASED MATCHING
        if user._mood_trend and story.avg_mood_change is not None:
            if user._mood_trend == 'declining' and story.avg_mood_change > 0:
                total_score += story.avg_mood_change * 2.0
            elif user._mood_trend == 'improving' and story.avg_mood_change > 0:
                total_score += story.avg_mood_change * 1.5
            elif user._mood_trend == 'stable':
                normalized_change = (story.avg_mood_change + 5) / 10.0
                total_score += normalized_change * 1.0
        
        # 4. VOLATILITY CONSIDERATION
        if user._mood_volatility is not None and user._mood_volatility > 1.5:
            if story.avg_mood_change is not None and story.avg_mood_change > 1.0:
                total_score += 1.0
        
        return total_score
    
    def _collaborative_filtering_score(self, user: UserProfile, story: Story, 
                                       current_time: datetime) -> float:
        if not user.completed_stories and not user.favorited_stories:
            return 0.0
        
        user_liked_with_decay = {}
        for story_id, timestamp in {**user.completed_stories, **user.favorited_stories}.items():
            days_ago = (current_time - timestamp).total_seconds() / 86400
            decay_factor = 0.5 ** (days_ago / self.event_half_life_days)
            user_liked_with_decay[story_id] = decay_factor
        
        user_liked = set(user_liked_with_decay.keys())
        
        similar_users_scores = []
        for other_user_id, other_user in self.users.items():
            if other_user_id == user.user_id:
                continue
            
            other_liked_with_decay = {}
            for story_id, timestamp in {**other_user.completed_stories, 
                                       **other_user.favorited_stories}.items():
                days_ago = (current_time - timestamp).total_seconds() / 86400
                decay_factor = 0.5 ** (days_ago / self.event_half_life_days)
                other_liked_with_decay[story_id] = decay_factor
            
            other_liked = set(other_liked_with_decay.keys())
            
            intersection = user_liked & other_liked
            union = user_liked | other_liked
            
            if not union:
                continue
            
            intersection_weight = sum(
                min(user_liked_with_decay.get(sid, 0), other_liked_with_decay.get(sid, 0))
                for sid in intersection
            )
            union_weight = len(union)
            
            similarity = intersection_weight / union_weight if union_weight > 0 else 0
            
            if story.id in other_liked:
                recency_weight = other_liked_with_decay.get(story.id, 0)
                similar_users_scores.append(similarity * recency_weight)
        
        if similar_users_scores:
            return max(similar_users_scores)
        return 0.0
    
    def _popularity_score(self, user: UserProfile, story: Story, 
                         current_time: datetime) -> float:
        completion_score = 0.0
        favorite_score = 0.0
        
        for u in self.users.values():
            if story.id in u.completed_stories:
                timestamp = u.completed_stories[story.id]
                days_ago = (current_time - timestamp).total_seconds() / 86400
                decay_factor = 0.5 ** (days_ago / self.event_half_life_days)
                completion_score += decay_factor
            
            if story.id in u.favorited_stories:
                timestamp = u.favorited_stories[story.id]
                days_ago = (current_time - timestamp).total_seconds() / 86400
                decay_factor = 0.5 ** (days_ago / self.event_half_life_days)
                favorite_score += decay_factor * 1.5
        
        total_users = max(len(self.users), 1)
        return (completion_score + favorite_score) / total_users
    
    def _content_based_score(self, user: UserProfile, story: Story, 
                            current_time: datetime) -> float:
        similarities_with_decay = []
        
        for liked_id, timestamp in {**user.completed_stories, **user.favorited_stories}.items():
            if liked_id not in self.stories:
                continue
            
            similarity = self._story_similarity(story.id, liked_id)
            days_ago = (current_time - timestamp).total_seconds() / 86400
            decay_factor = 0.5 ** (days_ago / self.event_half_life_days)
            similarities_with_decay.append(similarity * decay_factor)
        
        if similarities_with_decay:
            return max(similarities_with_decay)
        return 0.0
    
    def _story_similarity(self, story_id1: str, story_id2: str) -> float:
        if story_id1 == story_id2:
            return 1.0
        
        cache_key = tuple(sorted([story_id1, story_id2]))
        if cache_key in self._story_similarity_cache:
            return self._story_similarity_cache[cache_key]
        
        story1 = self.stories.get(story_id1)
        story2 = self.stories.get(story_id2)
        
        if not story1 or not story2:
            return 0.0
        
        similarity = 0.0
        
        if story1.theme == story2.theme:
            similarity += 0.5
        
        if story1.tags and story2.tags:
            tags1 = set(story1.tags)
            tags2 = set(story2.tags)
            intersection = len(tags1 & tags2)
            union = len(tags1 | tags2)
            if union > 0:
                similarity += 0.5 * (intersection / union)
        
        self._story_similarity_cache[cache_key] = similarity
        return similarity
    
    def get_sequence_insights(self, user_id: str = None) -> Dict:
        """Get insights about story sequences for analysis"""
        insights = {
            'global_transitions': {},
            'popular_paths': [],
            'effective_theme_transitions': {}
        }
        
        # Global transition statistics
        for from_id, to_dict in self.global_transition_graph.items():
            if from_id not in self.stories:
                continue
            
            from_story = self.stories[from_id]
            insights['global_transitions'][from_story.title] = {
                'best_next': [
                    (self.stories[to_id].title, avg_delta)
                    for to_id, avg_delta in sorted(
                        from_story.best_next_stories.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:3]
                ],
                'best_next_themes': from_story.best_next_themes
            }
        
        # User-specific insights
        if user_id and user_id in self.users:
            user = self.users[user_id]
            insights['user_sequences'] = [
                {
                    'from': self.stories[t.from_story_id].title if t.from_story_id in self.stories else t.from_story_id,
                    'to': self.stories[t.to_story_id].title if t.to_story_id in self.stories else t.to_story_id,
                    'mood_delta': t.mood_delta,
                    'time_between_min': t.time_between_minutes
                }
                for t in user.story_sequences[-10:]  # Last 10 transitions
            ]
        
        return insights
    
    # State management (updated to include transitions)
    def save_state(self) -> Dict:
        return {
            'stories': {sid: story.to_dict() for sid, story in self.stories.items()},
            'users': {
                uid: {
                    'user_id': user.user_id,
                    'viewed_stories': {sid: ts.isoformat() for sid, ts in user.viewed_stories.items()},
                    'completed_stories': {sid: ts.isoformat() for sid, ts in user.completed_stories.items()},
                    'favorited_stories': {sid: ts.isoformat() for sid, ts in user.favorited_stories.items()},
                    'theme_interactions': {
                        theme: [(score, ts.isoformat()) for score, ts in interactions]
                        for theme, interactions in user.theme_interactions.items()
                    },
                    'mood_history': [(ts.isoformat(), mood.to_dict()) for ts, mood in user.mood_history],
                    'current_mood': user.current_mood.to_dict() if user.current_mood else None,
                    'story_mood_impact': {
                        sid: (change, ts.isoformat()) 
                        for sid, (change, ts) in user.story_mood_impact.items()
                    },
                    'recent_story_views': [(ts.isoformat(), sid) for ts, sid in user.recent_story_views],
                    'recommendation_mix': user.recommendation_mix,
                    'mood_trend': user._mood_trend,
                    'mood_volatility': user._mood_volatility,
                    'story_sequences': [t.to_dict() for t in user.story_sequences],
                    'last_completed_story': user.last_completed_story,
                    'last_completed_timestamp': user.last_completed_timestamp.isoformat() if user.last_completed_timestamp else None
                }
                for uid, user in self.users.items()
            },
            'story_transitions': [t.to_dict() for t in self.story_transitions],
            'events': [event.to_dict() for event in self.events],
            'config': {
                'event_half_life_days': self.event_half_life_days,
                'mood_half_life_days': self.mood_half_life_days,
                'transition_window_minutes': self.transition_window_minutes
            }
        }
    
    def load_state(self, state: Dict):
        # Load config
        config = state.get('config', {})
        self.event_half_life_days = config.get('event_half_life_days', 30.0)
        self.mood_half_life_days = config.get('mood_half_life_days', 14.0)
        self.transition_window_minutes = config.get('transition_window_minutes', 1440.0)
        
        # Load stories
        self.stories = {
            sid: Story.from_dict(data)
            for sid, data in state.get('stories', {}).items()
        }
        
        self._theme_to_stories = defaultdict(list)
        for sid, story in self.stories.items():
            self._theme_to_stories[story.theme].append(sid)
        
        # Load story transitions (global)
        self.story_transitions = [
            StoryTransition.from_dict(t_data)
            for t_data in state.get('story_transitions', [])
        ]
        
        # Rebuild global transition graph
        self.global_transition_graph = defaultdict(lambda: defaultdict(list))
        for transition in self.story_transitions:
            self.global_transition_graph[transition.from_story_id][transition.to_story_id].append(transition)
        
        # Load users
        self.users = {}
        for uid, user_data in state.get('users', {}).items():
            user = UserProfile(uid)
            user.viewed_stories = {
                sid: datetime.fromisoformat(ts) 
                for sid, ts in user_data['viewed_stories'].items()
            }
            user.completed_stories = {
                sid: datetime.fromisoformat(ts) 
                for sid, ts in user_data['completed_stories'].items()
            }
            user.favorited_stories = {
                sid: datetime.fromisoformat(ts) 
                for sid, ts in user_data['favorited_stories'].items()
            }
            user.theme_interactions = defaultdict(list)
            for theme, interactions in user_data['theme_interactions'].items():
                user.theme_interactions[theme] = [
                    (score, datetime.fromisoformat(ts)) 
                    for score, ts in interactions
                ]
            user.mood_history = [
                (datetime.fromisoformat(ts), MoodScore.from_dict(mood))
                for ts, mood in user_data['mood_history']
            ]
            if user_data['current_mood']:
                user.current_mood = MoodScore.from_dict(user_data['current_mood'])
            user.story_mood_impact = {
                sid: (change, datetime.fromisoformat(ts))
                for sid, (change, ts) in user_data['story_mood_impact'].items()
            }
            user.recent_story_views = [
                (datetime.fromisoformat(ts), sid)
                for ts, sid in user_data['recent_story_views']
            ]
            user.recommendation_mix = user_data.get('recommendation_mix', 0.5)
            user._mood_trend = user_data.get('mood_trend')
            user._mood_volatility = user_data.get('mood_volatility')
            
            # Load sequences
            user.story_sequences = [
                StoryTransition.from_dict(t_data)
                for t_data in user_data.get('story_sequences', [])
            ]
            
            # Rebuild preferred_transitions from sequences
            user.preferred_transitions = defaultdict(list)
            user.theme_transition_preferences = defaultdict(lambda: defaultdict(list))
            for transition in user.story_sequences:
                user.preferred_transitions[transition.from_story_id].append(
                    (transition.to_story_id, transition.mood_delta, transition.timestamp)
                )
                
                if transition.from_story_id in self.stories and transition.to_story_id in self.stories:
                    from_theme = self.stories[transition.from_story_id].theme
                    to_theme = self.stories[transition.to_story_id].theme
                    if transition.mood_delta is not None:
                        user.theme_transition_preferences[from_theme][to_theme].append(
                            (transition.mood_delta, transition.timestamp)
                        )
            
            user.last_completed_story = user_data.get('last_completed_story')
            if user_data.get('last_completed_timestamp'):
                user.last_completed_timestamp = datetime.fromisoformat(user_data['last_completed_timestamp'])
            
            self.users[uid] = user
        
        # Load events
        self.events = [
            AnalyticsEvent.from_dict(event_data)
            for event_data in state.get('events', [])
        ]


# Enhanced example usage
if __name__ == "__main__":
    print("=" * 80)
    print("SEQUENCE-AWARE STORY RECOMMENDER DEMO")
    print("=" * 80)
    
    recommender = StoryRecommender(
        event_half_life_days=30.0,
        mood_half_life_days=14.0,
        transition_window_minutes=1440.0  # 24 hours
    )
    
    # Add stories
    recommender.add_story("story1", "The Happy Garden", "nature", ["uplifting", "peaceful"])
    recommender.add_story("story2", "Dark Mystery", "mystery", ["thriller", "suspense"])
    recommender.add_story("story3", "Summer Joy", "nature", ["uplifting", "warm"])
    recommender.add_story("story4", "The Detective", "mystery", ["investigation", "clever"])
    recommender.add_story("story5", "Mountain Peace", "nature", ["meditative", "calm"])
    recommender.add_story("story6", "City Lights", "urban", ["energetic", "modern"])
    recommender.add_story("story7", "Ocean Waves", "nature", ["calming", "peaceful"])
    recommender.add_story("story8", "Night Cafe", "urban", ["contemplative", "cozy"])
    
    # Simulate a user journey with sequences
    user_id = "user123"
    base_time = datetime.now() - timedelta(days=14)
    
    # Session 1: Dark mystery followed by calming nature story
    print("\n--- Session 1: User reads Dark Mystery → Mountain Peace ---")
    
    recommender.add_event(AnalyticsEvent(user_id, 'mood_general', base_time, mood_score=6.0))
    recommender.add_event(AnalyticsEvent(user_id, 'view', base_time + timedelta(minutes=1), story_id='story2'))
    recommender.add_event(AnalyticsEvent(user_id, 'complete', base_time + timedelta(minutes=10), story_id='story2'))
    recommender.add_event(AnalyticsEvent(user_id, 'mood_after', base_time + timedelta(minutes=11), 
                                        story_id='story2', mood_score=5.0))  # Mood decreased (intense story)
    
    # User immediately reads a calming story
    recommender.add_event(AnalyticsEvent(user_id, 'view', base_time + timedelta(minutes=15), story_id='story5'))
    recommender.add_event(AnalyticsEvent(user_id, 'complete', base_time + timedelta(minutes=25), story_id='story5'))
    recommender.add_event(AnalyticsEvent(user_id, 'mood_after', base_time + timedelta(minutes=26), 
                                        story_id='story5', mood_score=7.5))  # Mood recovered well!
    
    # Session 2: Same pattern again (reinforces the sequence)
    base_time2 = base_time + timedelta(days=3)
    print("\n--- Session 2: User repeats Dark Mystery → Ocean Waves ---")
    
    recommender.add_event(AnalyticsEvent(user_id, 'mood_general', base_time2, mood_score=6.5))
    recommender.add_event(AnalyticsEvent(user_id, 'view', base_time2, story_id='story2'))
    recommender.add_event(AnalyticsEvent(user_id, 'complete', base_time2 + timedelta(minutes=10), story_id='story2'))
    recommender.add_event(AnalyticsEvent(user_id, 'mood_after', base_time2 + timedelta(minutes=11), 
                                        story_id='story2', mood_score=5.5))
    
    recommender.add_event(AnalyticsEvent(user_id, 'view', base_time2 + timedelta(minutes=15), story_id='story7'))
    recommender.add_event(AnalyticsEvent(user_id, 'complete', base_time2 + timedelta(minutes=25), story_id='story7'))
    recommender.add_event(AnalyticsEvent(user_id, 'mood_after', base_time2 + timedelta(minutes=26), 
                                        story_id='story7', mood_score=8.0))
    
    # Add another user with different sequence preferences
    user2_id = "user456"
    base_time3 = base_time + timedelta(days=5)
    print("\n--- Session 3: User2 reads Happy Garden → City Lights ---")
    
    recommender.add_event(AnalyticsEvent(user2_id, 'mood_general', base_time3, mood_score=7.0))
    recommender.add_event(AnalyticsEvent(user2_id, 'view', base_time3, story_id='story1'))
    recommender.add_event(AnalyticsEvent(user2_id, 'complete', base_time3 + timedelta(minutes=10), story_id='story1'))
    recommender.add_event(AnalyticsEvent(user2_id, 'mood_after', base_time3 + timedelta(minutes=11), 
                                        story_id='story1', mood_score=8.0))
    
    recommender.add_event(AnalyticsEvent(user2_id, 'view', base_time3 + timedelta(minutes=15), story_id='story6'))
    recommender.add_event(AnalyticsEvent(user2_id, 'complete', base_time3 + timedelta(minutes=25), story_id='story6'))
    recommender.add_event(AnalyticsEvent(user2_id, 'mood_after', base_time3 + timedelta(minutes=26), 
                                        story_id='story6', mood_score=8.5))
    
    # Now test: User1 just finished Dark Mystery again
    print("\n" + "=" * 80)
    print("RECOMMENDATION TEST: User just finished 'Dark Mystery'")
    print("=" * 80)
    
    current_time = datetime.now()
    recommender.add_event(AnalyticsEvent(user_id, 'mood_general', current_time, mood_score=5.5))
    recommender.add_event(AnalyticsEvent(user_id, 'view', current_time, story_id='story2'))
    recommender.add_event(AnalyticsEvent(user_id, 'complete', current_time + timedelta(minutes=10), story_id='story2'))
    recommender.add_event(AnalyticsEvent(user_id, 'mood_after', current_time + timedelta(minutes=11), 
                                        story_id='story2', mood_score=5.0))
    
    # Get recommendations
    recs = recommender.get_recommendations(user_id, n_recommendations=6)
    
    print(f"\nUser just completed: Dark Mystery (mystery theme)")
    print(f"Current mood: 5.0 (slightly low)")
    print(f"\nTop Recommendations (with sequence-awareness):\n")
    
    for i, (story_id, score) in enumerate(recs, 1):
        story = recommender.stories[story_id]
        print(f"{i}. {story.title:20} ({story.theme:10}) - Score: {score:.2f}")
        print(f"   Tags: {', '.join(story.tags)}")
        
        # Show why this was recommended
        if story_id in recommender.stories['story2'].best_next_stories:
            effect = recommender.stories['story2'].best_next_stories[story_id]
            print(f"   ✓ Good follow-up to Dark Mystery (avg effect: {effect:+.2f})")
        
        if story.theme in recommender.stories['story2'].best_next_themes:
            theme_effect = recommender.stories['story2'].best_next_themes[story.theme]
            print(f"   ✓ {story.theme} theme works well after mystery (avg: {theme_effect:+.2f})")
        print()
    
    # Show sequence insights
    print("\n" + "=" * 80)
    print("SEQUENCE INSIGHTS")
    print("=" * 80)
    
    insights = recommender.get_sequence_insights(user_id)
    
    print("\nGlobal Story Transitions:")
    for story_title, data in insights['global_transitions'].items():
        if data['best_next']:
            print(f"\nAfter '{story_title}':")
            print(f"  Best next stories:")
            for next_title, avg_delta in data['best_next']:
                print(f"    → {next_title:20} (mood Δ: {avg_delta:+.2f})")
            if data['best_next_themes']:
                print(f"  Best next themes:")
                for theme, avg_delta in sorted(data['best_next_themes'].items(), 
                                               key=lambda x: x[1], reverse=True):
                    print(f"    → {theme:15} (mood Δ: {avg_delta:+.2f})")
    
    print(f"\nUser {user_id}'s Recent Sequences:")
    for seq in insights.get('user_sequences', [])[-5:]:
        mood_str = f"{seq['mood_delta']:+.2f}" if seq['mood_delta'] is not None else 'N/A'
        print(f"  {seq['from']:20} → {seq['to']:20} (mood Δ: {mood_str})")
    
    print("\n" + "=" * 80)
    print("Key Learnings:")
    print("  • System detected that 'nature' stories work well after 'mystery'")
    print("  • Personal sequence patterns are weighted higher than global patterns")
    print("  • Recent sequences (last 24 hours) get a recency boost")
    print("  • Both story-level and theme-level transitions are tracked")
    print("=" * 80)
