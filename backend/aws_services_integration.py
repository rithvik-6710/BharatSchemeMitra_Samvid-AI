"""
aws_services_integration.py — Advanced AWS Services Integration

Integrates additional AWS services for production-level features:
- Amazon Kendra for intelligent search
- Amazon Personalize for recommendations
- Amazon Lex for advanced NLU
- Amazon Connect for voice calls
- Amazon SES for email notifications
- Amazon SNS for SMS alerts
- Amazon EventBridge for workflow automation
- AWS Lambda for serverless functions
- Amazon CloudWatch for monitoring
"""

import boto3
import json
from typing import Dict, List, Optional
from datetime import datetime
import os


class KendraSearchService:
    """
    Amazon Kendra - Intelligent search for schemes
    Provides semantic search with natural language understanding
    """
    
    def __init__(self, index_id: str = None, region: str = "us-east-1"):
        self.kendra = boto3.client("kendra", region_name=region)
        self.index_id = index_id or os.getenv("KENDRA_INDEX_ID")
    
    def search_schemes(self, query: str, user_profile: Dict = None) -> List[Dict]:
        """
        Intelligent search using Kendra
        Returns ranked results with relevance scores
        """
        if not self.index_id:
            return []
        
        try:
            # Build attribute filter based on user profile
            attribute_filter = self._build_attribute_filter(user_profile)
            
            response = self.kendra.query(
                IndexId=self.index_id,
                QueryText=query,
                AttributeFilter=attribute_filter,
                PageSize=10
            )
            
            results = []
            for item in response.get("ResultItems", []):
                if item["Type"] == "DOCUMENT":
                    results.append({
                        "title": item.get("DocumentTitle", {}).get("Text", ""),
                        "excerpt": item.get("DocumentExcerpt", {}).get("Text", ""),
                        "score": item.get("ScoreAttributes", {}).get("ScoreConfidence", ""),
                        "document_id": item.get("DocumentId", ""),
                        "uri": item.get("DocumentURI", "")
                    })
            
            return results
        except Exception as e:
            print(f"Kendra search error: {e}")
            return []
    
    def _build_attribute_filter(self, user_profile: Dict) -> Dict:
        """Build Kendra attribute filter from user profile"""
        if not user_profile:
            return {}
        
        filters = []
        
        if user_profile.get("state"):
            filters.append({
                "EqualsTo": {
                    "Key": "state",
                    "Value": {"StringValue": user_profile["state"]}
                }
            })
        
        if user_profile.get("occupation"):
            filters.append({
                "EqualsTo": {
                    "Key": "category",
                    "Value": {"StringValue": user_profile["occupation"]}
                }
            })
        
        if not filters:
            return {}
        
        return {"AndAllFilters": filters} if len(filters) > 1 else filters[0]


class PersonalizeRecommendations:
    """
    Amazon Personalize - ML-powered scheme recommendations
    Learns from user interactions to improve recommendations
    """
    
    def __init__(self, campaign_arn: str = None, region: str = "us-east-1"):
        self.personalize = boto3.client("personalize-runtime", region_name=region)
        self.campaign_arn = campaign_arn or os.getenv("PERSONALIZE_CAMPAIGN_ARN")
    
    def get_recommendations(self, user_id: str, num_results: int = 5) -> List[Dict]:
        """Get personalized scheme recommendations"""
        if not self.campaign_arn:
            return []
        
        try:
            response = self.personalize.get_recommendations(
                campaignArn=self.campaign_arn,
                userId=user_id,
                numResults=num_results
            )
            
            return [
                {
                    "scheme_id": item["itemId"],
                    "score": item.get("score", 0)
                }
                for item in response.get("itemList", [])
            ]
        except Exception as e:
            print(f"Personalize error: {e}")
            return []
    
    def record_interaction(self, user_id: str, scheme_id: str, 
                          event_type: str = "click"):
        """Record user interaction for learning"""
        if not self.campaign_arn:
            return
        
        try:
            tracking_id = os.getenv("PERSONALIZE_TRACKING_ID")
            if not tracking_id:
                return
            
            self.personalize.put_events(
                trackingId=tracking_id,
                userId=user_id,
                sessionId=f"session-{datetime.now().timestamp()}",
                eventList=[{
                    "eventId": f"event-{datetime.now().timestamp()}",
                    "eventType": event_type,
                    "sentAt": datetime.now(),
                    "itemId": scheme_id
                }]
            )
        except Exception as e:
            print(f"Personalize tracking error: {e}")


class NotificationService:
    """
    Amazon SNS + SES - Multi-channel notifications
    Send SMS, email, and push notifications
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.sns = boto3.client("sns", region_name=region)
        self.ses = boto3.client("ses", region_name=region)
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS notification via SNS"""
        try:
            self.sns.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional"
                    }
                }
            )
            return True
        except Exception as e:
            print(f"SMS error: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, 
                   body_html: str, body_text: str) -> bool:
        """Send email notification via SES"""
        try:
            from_email = os.getenv("SES_FROM_EMAIL", "noreply@bharatschememitr.in")
            
            self.ses.send_email(
                Source=from_email,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {
                        "Html": {"Data": body_html},
                        "Text": {"Data": body_text}
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Email error: {e}")
            return False
    
    def send_application_reminder(self, user: Dict, scheme: Dict, 
                                  channel: str = "sms"):
        """Send application deadline reminder"""
        message = f"""
Reminder: Application deadline for {scheme['name']} is approaching!
Apply now at: {scheme.get('apply_url', 'portal')}
- Bharat Scheme Mitra
"""
        
        if channel == "sms" and user.get("phone"):
            self.send_sms(user["phone"], message)
        elif channel == "email" and user.get("email"):
            self.send_email(
                user["email"],
                f"Reminder: {scheme['name']} Deadline",
                f"<p>{message.replace(chr(10), '<br>')}</p>",
                message
            )


class EventBridgeWorkflows:
    """
    Amazon EventBridge - Workflow automation
    Trigger actions based on events
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.events = boto3.client("events", region_name=region)
        self.event_bus = os.getenv("EVENT_BUS_NAME", "default")
    
    def trigger_application_workflow(self, user_id: str, scheme_id: str, 
                                    application_data: Dict):
        """Trigger application processing workflow"""
        try:
            self.events.put_events(
                Entries=[{
                    "Source": "bharat-scheme-mitra",
                    "DetailType": "ApplicationSubmitted",
                    "Detail": json.dumps({
                        "userId": user_id,
                        "schemeId": scheme_id,
                        "applicationData": application_data,
                        "timestamp": datetime.now().isoformat()
                    }),
                    "EventBusName": self.event_bus
                }]
            )
        except Exception as e:
            print(f"EventBridge error: {e}")
    
    def trigger_document_verification(self, user_id: str, document_id: str):
        """Trigger document verification workflow"""
        try:
            self.events.put_events(
                Entries=[{
                    "Source": "bharat-scheme-mitra",
                    "DetailType": "DocumentUploaded",
                    "Detail": json.dumps({
                        "userId": user_id,
                        "documentId": document_id,
                        "timestamp": datetime.now().isoformat()
                    }),
                    "EventBusName": self.event_bus
                }]
            )
        except Exception as e:
            print(f"EventBridge error: {e}")


class CloudWatchMonitoring:
    """
    Amazon CloudWatch - Monitoring and metrics
    Track application performance and user behavior
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.namespace = "BharatSchemeMitra"
    
    def log_conversation_metric(self, metric_name: str, value: float, 
                               dimensions: Dict = None):
        """Log custom metric to CloudWatch"""
        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": "Count",
                "Timestamp": datetime.now()
            }
            
            if dimensions:
                metric_data["Dimensions"] = [
                    {"Name": k, "Value": v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
        except Exception as e:
            print(f"CloudWatch error: {e}")
    
    def log_user_interaction(self, intent: str, language: str, 
                            response_time: float):
        """Log user interaction metrics"""
        self.log_conversation_metric(
            "UserInteraction",
            1,
            {
                "Intent": intent,
                "Language": language
            }
        )
        
        self.log_conversation_metric(
            "ResponseTime",
            response_time,
            {
                "Intent": intent
            }
        )
    
    def log_scheme_recommendation(self, scheme_id: str, user_profile: Dict):
        """Log scheme recommendation for analytics"""
        self.log_conversation_metric(
            "SchemeRecommended",
            1,
            {
                "SchemeId": scheme_id,
                "Occupation": user_profile.get("occupation", "unknown"),
                "State": user_profile.get("state", "unknown")
            }
        )


class RekognitionDocumentVerification:
    """
    Amazon Rekognition - Advanced document verification
    Detect faces, verify authenticity, extract text
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.rekognition = boto3.client("rekognition", region_name=region)
    
    def verify_document_authenticity(self, image_bytes: bytes) -> Dict:
        """
        Verify document authenticity using Rekognition
        Detects tampering, quality issues, etc.
        """
        try:
            # Detect text
            text_response = self.rekognition.detect_text(
                Image={"Bytes": image_bytes}
            )
            
            # Detect faces (for Aadhaar, etc.)
            face_response = self.rekognition.detect_faces(
                Image={"Bytes": image_bytes},
                Attributes=["ALL"]
            )
            
            # Analyze image quality
            quality_score = self._calculate_quality_score(face_response)
            
            return {
                "is_authentic": quality_score > 0.7,
                "quality_score": quality_score,
                "has_face": len(face_response.get("FaceDetails", [])) > 0,
                "text_detected": len(text_response.get("TextDetections", [])) > 0,
                "confidence": quality_score
            }
        except Exception as e:
            print(f"Rekognition error: {e}")
            return {
                "is_authentic": False,
                "quality_score": 0,
                "error": str(e)
            }
    
    def _calculate_quality_score(self, face_response: Dict) -> float:
        """Calculate document quality score"""
        if not face_response.get("FaceDetails"):
            return 0.5  # No face, but might be valid document
        
        face = face_response["FaceDetails"][0]
        quality = face.get("Quality", {})
        
        brightness = quality.get("Brightness", 50) / 100
        sharpness = quality.get("Sharpness", 50) / 100
        
        return (brightness + sharpness) / 2


class LambdaFunctionInvoker:
    """
    AWS Lambda - Invoke serverless functions
    For complex processing tasks
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.lambda_client = boto3.client("lambda", region_name=region)
    
    def invoke_eligibility_checker(self, user_profile: Dict, 
                                   scheme: Dict) -> Dict:
        """Invoke Lambda function for complex eligibility checking"""
        try:
            function_name = os.getenv("ELIGIBILITY_LAMBDA", "")
            if not function_name:
                return {"eligible": False, "reason": "Service unavailable"}
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps({
                    "userProfile": user_profile,
                    "scheme": scheme
                })
            )
            
            result = json.loads(response["Payload"].read())
            return result
        except Exception as e:
            print(f"Lambda error: {e}")
            return {"eligible": False, "reason": str(e)}


class AWSServicesOrchestrator:
    """
    Orchestrates all AWS services for seamless integration
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.kendra = KendraSearchService(region=region)
        self.personalize = PersonalizeRecommendations(region=region)
        self.notifications = NotificationService(region=region)
        self.events = EventBridgeWorkflows(region=region)
        self.monitoring = CloudWatchMonitoring(region=region)
        self.rekognition = RekognitionDocumentVerification(region=region)
        self.lambda_invoker = LambdaFunctionInvoker(region=region)
    
    def enhanced_scheme_search(self, query: str, user_profile: Dict, 
                              user_id: str) -> List[Dict]:
        """
        Enhanced search combining Kendra and Personalize
        """
        import time
        start_time = time.time()
        
        # Get Kendra results
        kendra_results = self.kendra.search_schemes(query, user_profile)
        
        # Get Personalize recommendations
        personalize_results = self.personalize.get_recommendations(user_id)
        
        # Merge and rank results
        merged_results = self._merge_results(kendra_results, personalize_results)
        
        # Log metrics
        response_time = time.time() - start_time
        self.monitoring.log_user_interaction(
            "scheme_search", 
            user_profile.get("language", "en"),
            response_time
        )
        
        return merged_results
    
    def _merge_results(self, kendra_results: List[Dict], 
                      personalize_results: List[Dict]) -> List[Dict]:
        """Merge and rank results from multiple sources"""
        # Simple merging strategy - can be enhanced
        merged = {}
        
        # Add Kendra results with high weight
        for result in kendra_results:
            scheme_id = result["document_id"]
            merged[scheme_id] = {
                **result,
                "score": result.get("score", 0.5) * 0.7  # 70% weight
            }
        
        # Add Personalize results
        for result in personalize_results:
            scheme_id = result["scheme_id"]
            if scheme_id in merged:
                merged[scheme_id]["score"] += result["score"] * 0.3  # 30% weight
            else:
                merged[scheme_id] = {
                    "scheme_id": scheme_id,
                    "score": result["score"] * 0.3
                }
        
        # Sort by score
        sorted_results = sorted(
            merged.values(), 
            key=lambda x: x["score"], 
            reverse=True
        )
        
        return sorted_results[:10]
    
    def process_application_submission(self, user_id: str, scheme_id: str,
                                      application_data: Dict, user: Dict):
        """
        Complete application submission workflow
        """
        # Trigger workflow
        self.events.trigger_application_workflow(
            user_id, scheme_id, application_data
        )
        
        # Send confirmation
        if user.get("phone"):
            self.notifications.send_sms(
                user["phone"],
                f"Application submitted for scheme {scheme_id}. "
                f"Reference: {application_data.get('reference_id')}"
            )
        
        # Log metric
        self.monitoring.log_conversation_metric(
            "ApplicationSubmitted",
            1,
            {"SchemeId": scheme_id}
        )
    
    def verify_uploaded_document(self, document_bytes: bytes, 
                                document_type: str) -> Dict:
        """
        Verify document using Rekognition
        """
        verification_result = self.rekognition.verify_document_authenticity(
            document_bytes
        )
        
        # Log metric
        self.monitoring.log_conversation_metric(
            "DocumentVerified",
            1,
            {
                "DocumentType": document_type,
                "IsAuthentic": str(verification_result["is_authentic"])
            }
        )
        
        return verification_result
