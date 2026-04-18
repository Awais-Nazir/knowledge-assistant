FROM python:3.12-slim

WORKDIR /app

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# install dependencies
RUN uv sync --frozen --no-dev

# copy application code
COPY . .

# create uploads directory
RUN mkdir -p uploads

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]