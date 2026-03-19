"""
Database Models using SQLAlchemy ORM
Structured storage for analytics data
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


# ===== MODELS =====

class Channel(Base):
    """YouTube/TikTok Channel information"""
    __tablename__ = 'channels'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(20), nullable=False)  # 'youtube' or 'tiktok'
    channel_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(100))
    display_name = Column(String(200))
    subscriber_count = Column(Integer)
    total_videos = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    videos = relationship("Video", back_populates="channel", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="channel", cascade="all, delete-orphan")


class Video(Base):
    """Video information"""
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(100), unique=True, nullable=False)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    
    title = Column(String(500))
    description = Column(Text)
    published_at = Column(DateTime)
    duration = Column(Integer)  # seconds
    
    # Stats
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)
    
    # Calculated metrics
    engagement_rate = Column(Float)
    virality_score = Column(Float)
    
    # Metadata
    tags = Column(JSON)  # Store as JSON array
    category = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    channel = relationship("Channel", back_populates="videos")
    comments = relationship("Comment", back_populates="video", cascade="all, delete-orphan")


class Comment(Base):
    """Comment information"""
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    comment_id = Column(String(100), unique=True, nullable=False)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    
    author = Column(String(200))
    text = Column(Text)
    like_count = Column(Integer, default=0)
    published_at = Column(DateTime)
    
    # Sentiment analysis results
    sentiment = Column(String(20))  # 'positive', 'negative', 'neutral'
    sentiment_score = Column(Float)
    sentiment_confidence = Column(Float)
    emotion = Column(String(50))  # 'joy', 'admiration', etc.
    
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    video = relationship("Video", back_populates="comments")


class Analysis(Base):
    """Analysis run metadata"""
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    
    analysis_type = Column(String(50))  # 'comprehensive', 'sentiment', 'metrics'
    videos_analyzed = Column(Integer)
    comments_analyzed = Column(Integer)
    
    # Results summary
    avg_engagement_rate = Column(Float)
    positive_rate = Column(Float)
    negative_rate = Column(Float)
    neutral_rate = Column(Float)
    
    # File paths
    output_file = Column(String(500))
    
    # Timing
    duration_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    channel = relationship("Channel", back_populates="analyses")


# ===== DATABASE MANAGER =====

class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self, db_url: str = "sqlite:///analytics.db"):
        """
        Initialize database connection
        
        Args:
            db_url: SQLAlchemy database URL
        """
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_channel(self, platform: str, channel_id: str, **kwargs):
        """Add or update channel"""
        channel = self.session.query(Channel).filter_by(channel_id=channel_id).first()
        
        if not channel:
            channel = Channel(platform=platform, channel_id=channel_id, **kwargs)
            self.session.add(channel)
        else:
            for key, value in kwargs.items():
                setattr(channel, key, value)
            channel.updated_at = datetime.now()
        
        self.session.commit()
        return channel
    
    def add_video(self, video_id: str, channel_id: int, **kwargs):
        """Add or update video"""
        video = self.session.query(Video).filter_by(video_id=video_id).first()
        
        if not video:
            video = Video(video_id=video_id, channel_id=channel_id, **kwargs)
            self.session.add(video)
        else:
            for key, value in kwargs.items():
                setattr(video, key, value)
            video.updated_at = datetime.now()
        
        self.session.commit()
        return video
    
    def add_comment(self, comment_id: str, video_id: int, **kwargs):
        """Add comment"""
        comment = self.session.query(Comment).filter_by(comment_id=comment_id).first()
        
        if not comment:
            comment = Comment(comment_id=comment_id, video_id=video_id, **kwargs)
            self.session.add(comment)
            self.session.commit()
        
        return comment
    
    def add_analysis(self, channel_id: int, **kwargs):
        """Add analysis record"""
        analysis = Analysis(channel_id=channel_id, **kwargs)
        self.session.add(analysis)
        self.session.commit()
        return analysis
    
    def get_channel_stats(self, channel_id: str):
        """Get channel statistics"""
        channel = self.session.query(Channel).filter_by(channel_id=channel_id).first()
        
        if not channel:
            return None
        
        total_videos = len(channel.videos)
        total_comments = sum(len(video.comments) for video in channel.videos)
        avg_engagement = sum(v.engagement_rate or 0 for v in channel.videos) / max(total_videos, 1)
        
        return {
            'channel': channel,
            'total_videos': total_videos,
            'total_comments': total_comments,
            'avg_engagement': round(avg_engagement, 2)
        }
    
    def close(self):
        """Close database session"""
        self.session.close()


# ===== EXAMPLE USAGE =====

if __name__ == '__main__':
    # Initialize database
    db = DatabaseManager()
    
    # Add channel
    channel = db.add_channel(
        platform='youtube',
        channel_id='UCaxnllxL894OHbc_6VQcGmA',
        username='@travinhuniversity',
        display_name='Trường Đại học Trà Vinh',
        subscriber_count=15000
    )
    
    print(f"Created channel: {channel.display_name}")
    
    # Add video
    video = db.add_video(
        video_id='abc123',
        channel_id=channel.id,
        title='Test Video',
        view_count=1000,
        like_count=100,
        engagement_rate=10.0
    )
    
    print(f"Created video: {video.title}")
    
    # Get stats
    stats = db.get_channel_stats('UCaxnllxL894OHbc_6VQcGmA')
    print(f"Channel stats: {stats}")
    
    db.close()
