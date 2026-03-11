import requests
import sys
import json
from datetime import datetime

class AITicketHelperTester:
    def __init__(self, base_url="https://kb-ticket-sage.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/")
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'N/A')}"
            self.log_test("API Root Endpoint", success, details)
            return success
        except Exception as e:
            self.log_test("API Root Endpoint", False, f"Error: {str(e)}")
            return False

    def test_preprocess_endpoint(self):
        """Test preprocessing and anonymization"""
        test_ticket = "My email is john@example.com and phone is 555-123-4567. Transaction ID: TXN-12345"
        
        try:
            response = requests.post(f"{self.api_url}/preprocess", 
                                   json={"ticket_text": test_ticket})
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_sensitive = data.get('has_sensitive_data', False)
                anonymized = data.get('anonymized', '')
                
                # Check if sensitive data was detected and anonymized
                email_anonymized = '[EMAIL]' in anonymized
                phone_anonymized = '[PHONE]' in anonymized
                txn_anonymized = '[TRANSACTION_ID]' in anonymized
                
                details = f"Sensitive data detected: {has_sensitive}, Email anonymized: {email_anonymized}, Phone anonymized: {phone_anonymized}, TXN anonymized: {txn_anonymized}"
                success = has_sensitive and email_anonymized and phone_anonymized and txn_anonymized
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Preprocessing & Anonymization", success, details)
            return success
        except Exception as e:
            self.log_test("Preprocessing & Anonymization", False, f"Error: {str(e)}")
            return False

    def test_classification_endpoint(self):
        """Test ticket classification using LLaMA"""
        test_ticket = "My password reset link is not working. I clicked it multiple times but nothing happens."
        
        try:
            response = requests.post(f"{self.api_url}/classify", 
                                   json={"ticket_text": test_ticket})
            success = response.status_code == 200
            
            if success:
                data = response.json()
                category = data.get('category', '')
                confidence = data.get('confidence', 0)
                tags = data.get('tags', [])
                status = data.get('status', '')
                
                # Check if classification looks reasonable
                has_category = len(category) > 0
                has_confidence = 0 <= confidence <= 1
                has_tags = len(tags) > 0
                is_success = status == 'success'
                
                details = f"Category: {category}, Confidence: {confidence:.2f}, Tags: {tags}, Status: {status}"
                success = has_category and has_confidence and has_tags and is_success
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("LLaMA Classification", success, details)
            return success
        except Exception as e:
            self.log_test("LLaMA Classification", False, f"Error: {str(e)}")
            return False

    def test_recommendation_endpoint(self):
        """Test KB article recommendations via FAISS"""
        test_ticket = "I need help with password reset"
        
        try:
            response = requests.post(f"{self.api_url}/recommend", 
                                   json={"ticket_text": test_ticket, "top_k": 3})
            success = response.status_code == 200
            
            if success:
                data = response.json()
                recommendations = data.get('recommendations', [])
                count = data.get('count', 0)
                
                # Check if we got recommendations
                has_recommendations = len(recommendations) > 0
                count_matches = count == len(recommendations)
                
                # Check recommendation structure
                valid_structure = True
                if recommendations:
                    first_rec = recommendations[0]
                    required_fields = ['article_id', 'title', 'category', 'content', 'similarity_score', 'rank']
                    valid_structure = all(field in first_rec for field in required_fields)
                
                details = f"Recommendations: {count}, Valid structure: {valid_structure}"
                if recommendations:
                    details += f", Top similarity: {recommendations[0].get('similarity_score', 0):.3f}"
                
                success = has_recommendations and count_matches and valid_structure
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("FAISS KB Recommendations", success, details)
            return success
        except Exception as e:
            self.log_test("FAISS KB Recommendations", False, f"Error: {str(e)}")
            return False

    def test_analyze_ticket_endpoint(self):
        """Test full ticket analysis (preprocessing + classification + recommendations)"""
        test_ticket = "My API key sk-test-abc123 is not working. Getting 401 error when calling https://api.example.com"
        
        try:
            response = requests.post(f"{self.api_url}/analyze-ticket", 
                                   json={"ticket_text": test_ticket})
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Check all components are present
                has_preprocessed = 'preprocessed' in data
                has_classification = 'classification' in data
                has_recommendations = 'recommendations' in data
                
                # Check preprocessing worked
                preprocessed = data.get('preprocessed', {})
                sensitive_detected = preprocessed.get('has_sensitive_data', False)
                
                # Check classification worked
                classification = data.get('classification', {})
                has_category = len(classification.get('category', '')) > 0
                
                # Check recommendations worked
                recommendations = data.get('recommendations', [])
                has_recs = len(recommendations) > 0
                
                details = f"Preprocessed: {has_preprocessed}, Classification: {has_classification}, Recommendations: {has_recommendations}, Sensitive data: {sensitive_detected}, Category: {classification.get('category', 'N/A')}, Rec count: {len(recommendations)}"
                success = has_preprocessed and has_classification and has_recommendations and has_category
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Full Ticket Analysis", success, details)
            return success
        except Exception as e:
            self.log_test("Full Ticket Analysis", False, f"Error: {str(e)}")
            return False

    def test_gap_analysis_endpoint(self):
        """Test KB gap analysis"""
        try:
            response = requests.get(f"{self.api_url}/gap-analysis")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                
                # Check structure
                has_summary = 'summary' in data
                has_low_performers = 'low_performers' in data
                has_low_coverage = 'low_coverage' in data
                
                # Check summary metrics
                summary = data.get('summary', {})
                required_metrics = ['total_articles', 'avg_ctr', 'avg_views', 'avg_clicks', 'low_performers_count', 'low_coverage_count']
                has_all_metrics = all(metric in summary for metric in required_metrics)
                
                total_articles = summary.get('total_articles', 0)
                
                details = f"Summary: {has_summary}, Low performers: {has_low_performers}, Low coverage: {has_low_coverage}, Total articles: {total_articles}, All metrics: {has_all_metrics}"
                success = has_summary and has_low_performers and has_low_coverage and has_all_metrics and total_articles > 0
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("Gap Analysis", success, details)
            return success
        except Exception as e:
            self.log_test("Gap Analysis", False, f"Error: {str(e)}")
            return False

    def test_data_endpoints(self):
        """Test data retrieval endpoints"""
        success_count = 0
        
        # Test tickets endpoint
        try:
            response = requests.get(f"{self.api_url}/tickets")
            success = response.status_code == 200
            if success:
                data = response.json()
                tickets = data.get('tickets', [])
                count = data.get('count', 0)
                success = len(tickets) > 0 and count == len(tickets)
                details = f"Tickets loaded: {count}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Tickets Data Endpoint", success, details)
            if success:
                success_count += 1
        except Exception as e:
            self.log_test("Tickets Data Endpoint", False, f"Error: {str(e)}")
        
        # Test KB articles endpoint
        try:
            response = requests.get(f"{self.api_url}/kb-articles")
            success = response.status_code == 200
            if success:
                data = response.json()
                articles = data.get('articles', [])
                count = data.get('count', 0)
                success = len(articles) > 0 and count == len(articles)
                details = f"KB articles loaded: {count}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("KB Articles Data Endpoint", success, details)
            if success:
                success_count += 1
        except Exception as e:
            self.log_test("KB Articles Data Endpoint", False, f"Error: {str(e)}")
        
        return success_count == 2

    def test_build_index_endpoint(self):
        """Test FAISS index building endpoint"""
        try:
            response = requests.post(f"{self.api_url}/build-index")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                status = data.get('status', '')
                message = data.get('message', '')
                success = status == 'success'
                details = f"Status: {status}, Message: {message}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("FAISS Index Building", success, details)
            return success
        except Exception as e:
            self.log_test("FAISS Index Building", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting AI Support Ticket Helper Backend Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test basic connectivity
        if not self.test_api_root():
            print("❌ API not accessible. Stopping tests.")
            return False
        
        # Test individual components
        self.test_preprocess_endpoint()
        self.test_classification_endpoint()
        self.test_recommendation_endpoint()
        self.test_analyze_ticket_endpoint()
        self.test_gap_analysis_endpoint()
        self.test_data_endpoints()
        self.test_build_index_endpoint()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check details above.")
            return False

def main():
    tester = AITicketHelperTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())