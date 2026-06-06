"""集中配置管理"""

import os

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "eknowledge.db")
CHROMA_DB_PATH = os.path.join(DATA_DIR, "chromadb")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Ollama 配置
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:7b"
EMBEDDING_MODEL = "nomic-embed-text"

# JWT 配置
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 480  # 8 hours
JWT_REFRESH_THRESHOLD_MINUTES = 30

# 密码策略
PASSWORD_BCRYPT_COST = 12
PASSWORD_MIN_LENGTH = 8

# 登录安全
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCK_MINUTES = 15
LOGIN_RATE_LIMIT_PER_MINUTE = 10

# RAG 参数
RAG_TOP_K = 5
RAG_SIMILARITY_THRESHOLD = 0.65
RAG_MAX_RETRIES = 3
RAG_RETRY_INTERVAL_SECONDS = 5

# LLM 参数
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 1024
LLM_TIMEOUT_SECONDS = 30

# Embedding 参数
EMBEDDING_DIMENSION = 768

# ChromaDB 参数
CHROMA_COLLECTION_NAME = "faq_vectors"

# 向量化批处理（防止 Ollama 过载）
VECTORIZE_BATCH_SIZE = 10
VECTORIZE_BATCH_DELAY = 3  # 批次间休息秒数

# 分页
DEFAULT_PAGE_SIZE = 20

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
