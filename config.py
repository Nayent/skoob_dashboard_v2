"""
Configurações centralizadas do projeto.
Configuracoes editaveis do projeto.
"""
from pathlib import Path

# --- Token de Autenticação ---
# Cole aqui um token válido e não compartilhe este arquivo.
TOKEN: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY3YmQyMDUwNzBjNGFiYzMzNzAzOTc4NiIsImlhdCI6MTc4NTQ2OTYzMSwiZXhwIjoxNzg2NzY1NjMxfQ.mD-omIps97-jFxr2_tl02e7ZSHOXe6vaILtMz92ElvI"

# --- Paths ---
PROJECT_DIR = Path(__file__).resolve().parent
STAGE_DIR: str = str((PROJECT_DIR / "stage").resolve())

# --- API ---
API_URL: str = "https://prd-api.skoob.com.br/api/v1/bookshelf"
PAGE_LIMIT: int = 100
MAX_RETRIES: int = 3
REQUEST_TIMEOUT: int = 15  # segundos
