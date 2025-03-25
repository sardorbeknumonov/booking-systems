# Use the official Nginx image as a base image
FROM nginx:latest

# Remove the default Nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf

# Copy your custom configuration file to the correct directory
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static files from Django's static volume
COPY ./staticfiles /usr/share/nginx/html/static

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
