"""Tests for smart keyframe extractor"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from smart_keyframe_extractor import extract_top_k_keyframes, SmartKeyFrameExtractor


class TestSmartKeyFrameExtractor:
    """Test SmartKeyFrameExtractor class"""
    
    def test_initialization(self):
        """Test extractor initialization"""
        with patch.object(SmartKeyFrameExtractor, '_check_installations'):
            extractor = SmartKeyFrameExtractor()
            assert extractor.ffmpeg_path == "ffmpeg"
            assert extractor.ffprobe_path == "ffprobe"
    
    def test_get_resolution_params(self):
        """Test resolution parameter calculation"""
        with patch.object(SmartKeyFrameExtractor, '_check_installations'):
            extractor = SmartKeyFrameExtractor()
            
            # Test original resolution
            scale_filter, scale_params = extractor.get_resolution_params("original", 1920, 1080)
            assert scale_filter is None
            assert scale_params is None
            
            # Test 720p downscaling
            scale_filter, scale_params = extractor.get_resolution_params("720p", 1920, 1080)
            assert "scale=" in scale_filter
            assert "720" in scale_params or "1280" in scale_params
    
    def test_calculate_adaptive_frame_count(self):
        """Test adaptive frame count calculation"""
        with patch.object(SmartKeyFrameExtractor, '_check_installations'):
            extractor = SmartKeyFrameExtractor()
            
            # Test fixed mode
            count = extractor.calculate_adaptive_frame_count(60, mode="fixed", frames_per_interval=5)
            assert count == 5
            
            # Test adaptive mode for short video
            count = extractor.calculate_adaptive_frame_count(20, mode="adaptive")
            assert 3 <= count <= 5
            
            # Test interval mode
            count = extractor.calculate_adaptive_frame_count(60, mode="interval", interval=10, frames_per_interval=2)
            assert count >= 3


class TestExtractFunction:
    """Test main extract function"""
    
    def test_nonexistent_file(self):
        """Test with non-existent video file"""
        result = extract_top_k_keyframes("nonexistent.mp4")
        assert 'error' in result
        assert result['error'] == '视频文件不存在'
    
    def test_invalid_parameters(self):
        """Test with invalid parameters"""
        # Test with invalid k value
        with tempfile.NamedTemporaryFile(suffix='.mp4') as temp_file:
            # This will still fail because it's not a valid video, but tests parameter handling
            result = extract_top_k_keyframes(temp_file.name, k=-1)
            # Should handle the parameter correctly even if video processing fails


class TestVisionUtils:
    """Test vision utility functions"""
    
    def test_smart_resize(self):
        """Test smart resize function"""
        from smart_keyframe_extractor.vision_utils import smart_resize
        
        # Test normal resize
        h, w = smart_resize(1080, 1920)
        assert h % 28 == 0  # Should be divisible by factor
        assert w % 28 == 0
        
        # Test with extreme aspect ratio (should raise error)
        with pytest.raises(ValueError):
            smart_resize(100, 30000)  # Aspect ratio > 200
    
    def test_image_to_base64(self):
        """Test base64 conversion"""
        from smart_keyframe_extractor.vision_utils import image_to_base64, base64_to_image
        from PIL import Image
        import tempfile
        
        # Create a test image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            test_image.save(temp_file.name)
            
            # Test conversion to base64
            base64_str = image_to_base64(temp_file.name)
            assert isinstance(base64_str, str)
            assert len(base64_str) > 0
            
            # Test conversion back to image
            decoded_image = base64_to_image(base64_str)
            assert isinstance(decoded_image, Image.Image)
            
            # Cleanup
            os.unlink(temp_file.name)


class TestAzureOpenAI:
    """Test Azure OpenAI integration"""
    
    def test_azure_analyzer_initialization(self):
        """Test Azure OpenAI analyzer initialization"""
        from smart_keyframe_extractor.azure_openai import AzureOpenAIAnalyzer
        
        # Test with missing credentials
        with pytest.raises(ValueError):
            AzureOpenAIAnalyzer()
        
        # Test with provided credentials
        analyzer = AzureOpenAIAnalyzer(
            api_key="test_key",
            endpoint="https://test.openai.azure.com/"
        )
        assert analyzer.api_key == "test_key"
        assert analyzer.endpoint == "https://test.openai.azure.com/"
    
    @patch('smart_keyframe_extractor.azure_openai.AzureOpenAI')
    def test_analyze_video_frames(self, mock_azure_client):
        """Test video frame analysis"""
        from smart_keyframe_extractor.azure_openai import AzureOpenAIAnalyzer
        
        # Mock the Azure OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test analysis result"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_azure_client.return_value = mock_client_instance
        
        analyzer = AzureOpenAIAnalyzer(
            api_key="test_key",
            endpoint="https://test.openai.azure.com/"
        )
        
        test_frames = [
            {'base64': 'test_base64_data', 'timestamp': 0.0},
            {'base64': 'test_base64_data2', 'timestamp': 5.0}
        ]
        
        result = analyzer.analyze_video_frames(test_frames)
        
        assert result['success'] is True
        assert result['analysis'] == "Test analysis result"
        assert result['usage']['total_tokens'] == 150
        assert result['frames_analyzed'] == 2


if __name__ == "__main__":
    pytest.main([__file__])
