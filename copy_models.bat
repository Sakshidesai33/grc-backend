@echo off
echo Copying trained AI models from aifeatures to backend...
copy "..\aifeatures\flutter_ai_grc\backend\optimized_severity_model.pkl" "optimized_severity_model.pkl"
copy "..\aifeatures\flutter_ai_grc\backend\optimized_severity_vectorizer.pkl" "optimized_severity_vectorizer.pkl"
copy "..\aifeatures\flutter_ai_grc\backend\optimized_severity_encoder.pkl" "optimized_severity_encoder.pkl"
copy "..\aifeatures\flutter_ai_grc\backend\optimized_category_model.pkl" "optimized_category_model.pkl"
copy "..\aifeatures\flutter_ai_grc\backend\optimized_category_vectorizer.pkl" "optimized_category_vectorizer.pkl"
copy "..\aifeatures\flutter_ai_grc\backend\optimized_category_encoder.pkl" "optimized_category_encoder.pkl"
copy "..\aifeatures\flutter_ai_grc\backend\optimized_similarity_vectorizer.pkl" "optimized_similarity_vectorizer.pkl"
copy "..\aifeatures\flutter_ai_grc\backend\optimized_similarity_vectors.pkl" "optimized_similarity_vectors.pkl"
copy "..\aifeatures\flutter_ai_grc\backend\comprehensive_incident_dataset_1000.csv" "comprehensive_incident_dataset_1000.csv"
echo All models copied successfully!
pause
