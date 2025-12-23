FROM nginx:alpine

# Copy custom configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static assets
# . dockerignore should handle excluding python files if needed, but COPY . is simple
COPY . /usr/share/nginx/html

# Clean up unnecessary files (like serve_frontend.py)
RUN rm /usr/share/nginx/html/serve_frontend.py || true
