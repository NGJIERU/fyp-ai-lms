"""
Tests for AI Recommendation Service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.recommendation.recommendation_engine import RecommendationEngine
from app.services.processing.embedding_service import EmbeddingService
from app.services.processing.quality_scorer import QualityScorer


class TestQualityScorer:
    """Tests for the QualityScorer class."""
    
    def test_init_default_weights(self):
        """Test default weight initialization."""
        scorer = QualityScorer()
        assert sum(scorer.weights.values()) == pytest.approx(1.0)
    
    def test_init_custom_weights(self):
        """Test custom weight initialization."""
        custom_weights = {
            "domain_authority": 0.5,
            "popularity": 0.2,
            "recency": 0.1,
            "content_quality": 0.1,
            "relevance": 0.1
        }
        scorer = QualityScorer(weights=custom_weights)
        assert sum(scorer.weights.values()) == pytest.approx(1.0)
    
    def test_score_domain_authority_known_source(self):
        """Test domain authority scoring for known sources."""
        scorer = QualityScorer()
        material = {"source": "MIT OCW", "author": ""}
        score = scorer._score_domain_authority(material)
        assert score >= 0.9
    
    def test_score_domain_authority_unknown_source(self):
        """Test domain authority scoring for unknown sources."""
        scorer = QualityScorer()
        material = {"source": "Unknown Blog", "author": "Random Author"}
        score = scorer._score_domain_authority(material)
        assert score == 0.4  # Default score
    
    def test_score_popularity_video(self):
        """Test popularity scoring for video materials."""
        scorer = QualityScorer()
        material = {
            "type": "video",
            "metadata": {
                "view_count": 500000,
                "like_count": 25000
            }
        }
        score = scorer._score_popularity(material)
        assert 0.6 <= score <= 1.0
    
    def test_score_popularity_repository(self):
        """Test popularity scoring for repository materials."""
        scorer = QualityScorer()
        material = {
            "type": "repository",
            "metadata": {
                "stars": 5000,
                "forks": 500
            }
        }
        score = scorer._score_popularity(material)
        assert 0.5 <= score <= 1.0
    
    def test_score_recency_recent(self):
        """Test recency scoring for recent content."""
        scorer = QualityScorer()
        material = {"publish_date": datetime.now()}
        score = scorer._score_recency(material)
        assert score >= 0.9
    
    def test_score_recency_old(self):
        """Test recency scoring for old content."""
        scorer = QualityScorer()
        material = {"publish_date": datetime(2018, 1, 1)}
        score = scorer._score_recency(material)
        assert score <= 0.3
    
    def test_score_content_quality(self):
        """Test content quality scoring."""
        scorer = QualityScorer()
        material = {
            "title": "Complete Python Tutorial for Beginners - Step by Step Guide",
            "description": "A comprehensive guide to learning Python programming from scratch. " * 10,
            "content_text": "Full content here. " * 500,
            "author": "Expert Author",
            "metadata": {"has_transcript": True, "topics": ["python", "tutorial", "beginner"]}
        }
        score = scorer._score_content_quality(material)
        assert score >= 0.5
    
    def test_calculate_score_complete(self):
        """Test complete quality score calculation."""
        scorer = QualityScorer()
        material = {
            "source": "MIT OCW",
            "author": "Prof. Smith",
            "type": "video",
            "title": "Introduction to Machine Learning",
            "description": "A comprehensive course on ML fundamentals.",
            "content_text": "Course content...",
            "publish_date": datetime.now(),
            "metadata": {
                "view_count": 100000,
                "like_count": 5000,
                "has_transcript": True
            }
        }
        score = scorer.calculate_score(material, relevance_score=0.8)
        assert 0.0 <= score <= 1.0
    
    def test_get_score_breakdown(self):
        """Test getting score breakdown."""
        scorer = QualityScorer()
        material = {"source": "YouTube", "type": "video", "metadata": {}}
        breakdown = scorer.get_score_breakdown(material)
        assert "domain_authority" in breakdown
        assert "popularity" in breakdown
        assert "recency" in breakdown
        assert "content_quality" in breakdown
        assert "weights" in breakdown


class TestEmbeddingService:
    """Tests for the EmbeddingService class."""
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Create a mock embedding service."""
        with patch('app.services.processing.embedding_service.SentenceTransformer') as mock:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = [0.1] * 384
            mock.return_value = mock_model
            
            service = EmbeddingService(model_name="local_fast")
            return service
    
    def test_compute_similarity_identical(self):
        """Test similarity computation for identical vectors."""
        service = EmbeddingService.__new__(EmbeddingService)
        service.embedding_dim = 384
        
        vec = [1.0] * 384
        similarity = service.compute_similarity(vec, vec)
        assert similarity == pytest.approx(1.0)
    
    def test_compute_similarity_orthogonal(self):
        """Test similarity computation for orthogonal vectors."""
        service = EmbeddingService.__new__(EmbeddingService)
        service.embedding_dim = 4
        
        vec1 = [1.0, 0.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0, 0.0]
        similarity = service.compute_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.5)  # Normalized to 0-1
    
    def test_find_most_similar(self):
        """Test finding most similar embeddings."""
        service = EmbeddingService.__new__(EmbeddingService)
        service.embedding_dim = 4
        
        query = [1.0, 0.0, 0.0, 0.0]
        candidates = [
            [1.0, 0.0, 0.0, 0.0],  # Most similar
            [0.5, 0.5, 0.0, 0.0],  # Somewhat similar
            [0.0, 1.0, 0.0, 0.0],  # Less similar
        ]
        
        results = service.find_most_similar(query, candidates, top_k=2)
        assert len(results) == 2
        assert results[0][0] == 0  # First candidate is most similar
        assert results[0][1] > results[1][1]  # Scores are sorted


class TestRecommendationEngine:
    """Tests for the RecommendationEngine class."""
    
    @pytest.fixture
    def mock_engine(self):
        """Create a recommendation engine with mocked dependencies."""
        mock_embedding = Mock(spec=EmbeddingService)
        mock_embedding.embed_syllabus_topic.return_value = [0.1] * 384
        mock_embedding.embed_material.return_value = [0.1] * 384
        mock_embedding.compute_similarity.return_value = 0.8
        mock_embedding.embedding_dim = 384
        
        mock_scorer = Mock(spec=QualityScorer)
        
        engine = RecommendationEngine(
            embedding_service=mock_embedding,
            quality_scorer=mock_scorer
        )
        return engine
    
    def test_calculate_combined_score(self, mock_engine):
        """Test combined score calculation."""
        score = mock_engine._calculate_combined_score(
            similarity=0.8,
            quality=0.7,
            similarity_weight=0.6,
            quality_weight=0.4
        )
        expected = 0.8 * 0.6 + 0.7 * 0.4
        assert score == pytest.approx(expected)
    
    def test_calculate_combined_score_weights(self, mock_engine):
        """Test that weights affect the combined score correctly."""
        # Higher similarity weight
        score1 = mock_engine._calculate_combined_score(
            similarity=1.0,
            quality=0.0,
            similarity_weight=1.0,
            quality_weight=0.0
        )
        assert score1 == pytest.approx(1.0)
        
        # Higher quality weight
        score2 = mock_engine._calculate_combined_score(
            similarity=0.0,
            quality=1.0,
            similarity_weight=0.0,
            quality_weight=1.0
        )
        assert score2 == pytest.approx(1.0)


class TestIntegration:
    """Integration tests for recommendation system."""
    
    def test_quality_scorer_with_real_data(self):
        """Test quality scorer with realistic material data."""
        scorer = QualityScorer()
        
        # High quality material
        high_quality = {
            "source": "MIT OCW",
            "author": "Prof. John Guttag",
            "type": "video",
            "title": "Introduction to Computer Science and Programming Using Python",
            "description": "This course is the first of a two-course sequence: Introduction to Computer Science and Programming Using Python, and Introduction to Computational Thinking and Data Science. Together, they are designed to help people with no prior exposure to computer science or programming learn to think computationally and write programs to tackle useful problems.",
            "content_text": "Detailed course content..." * 100,
            "publish_date": datetime.now(),
            "metadata": {
                "view_count": 2000000,
                "like_count": 100000,
                "has_transcript": True,
                "topics": ["python", "programming", "computer science", "mit", "education"]
            }
        }
        
        # Low quality material
        low_quality = {
            "source": "Random Blog",
            "author": "",
            "type": "blog",
            "title": "Python",
            "description": "Learn Python.",
            "content_text": "",
            "publish_date": datetime(2015, 1, 1),
            "metadata": {}
        }
        
        high_score = scorer.calculate_score(high_quality, relevance_score=0.9)
        low_score = scorer.calculate_score(low_quality, relevance_score=0.3)
        
        assert high_score > low_score
        assert high_score >= 0.6
        assert low_score <= 0.4
