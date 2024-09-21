# Use the official Ubuntu image
FROM ubuntu:20.04

# Set non-interactive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary packages
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    vim \
    curl \
    && apt-get clean

# Create a new user (e.g., 'ubuntu') and add SSH access
RUN useradd -ms /bin/bash ubuntu && echo 'ubuntu:ubuntu' | chpasswd && usermod -aG sudo ubuntu

# Create SSH directory for the user
RUN mkdir -p /home/ubuntu/.ssh

# Use an argument to receive the public SSH key
ARG PUBLIC_SSH_KEY

# Add the public SSH key to authorized_keys
RUN echo "$PUBLIC_SSH_KEY" > /home/ubuntu/.ssh/authorized_keys

# Ensure correct permissions for the SSH keys
RUN chown -R ubuntu:ubuntu /home/ubuntu/.ssh && chmod 600 /home/ubuntu/.ssh/authorized_keys

# Configure SSH server
RUN sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config \
    && sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Expose port 22 for SSH
EXPOSE 22

# Allow additional ports via environment variables (e.g., PORTS="80 443")
ARG PORTS
RUN if [ -n "$PORTS" ]; then for port in $PORTS; do echo "Exposing port $port" && EXPOSE $port; done; fi

# Start SSH service
CMD ["/usr/sbin/sshd", "-D"]
