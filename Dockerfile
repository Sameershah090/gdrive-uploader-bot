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

# Create SSH directory for the user and add the public SSH key
RUN mkdir -p /home/ubuntu/.ssh
# Replace this line with your actual public SSH key
RUN echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCt6ynuab6T+Hd95dJT/BSAMyDlbYuw+YSkOOGSEte7xEeMY14L0Jxc6c5ttv/hXiZXPFCAJ2vDcZ5W8GVQsQc2zzwo1s0QzJjeWUomh+jE2VSqtcYdFWx6Gyb6kAj6YFrXetBDziqtP82Y8pRkJZxtEh0+F4cKR8zo9xtbgXz/v2bR3cGxv9vmPq2i5I0wuS0RznBdDhwMizwpDeEWv4WqXHVjbDjAky0O8sJqRNY6BIq4ofcfd7uYF1Lj0hlsbkRcVrLM1n5090ziwAKu4hXiImOMok2j2PlUblB9bUro4BLO2M00+a1WEuuiOSkK/tM9cfIF9zOXo0gcFIcFG4hLreC4hFh8B71gqVBJfW4SAkmcUjw3Msx/i3j6GlIB/GMW2bcCL3syTjtti2DPCw7YDTIN7Wu5sWfYl+z3agQqZseTQ0EcjRZue3KdE7ipL1Tcaj8xqcYvHzzBfnhj+P+Tp4GX80hqR6HlXKOONuvbKhSC+pWpt8dmebt8gH6qi52F/6rDPSjGNsBj+q7/uScYFtS0s2BxBrLpBBNR8+s5fY4TmOWj/slbtaCuIMqnvR9lWiU63l0tVjoBnUhZ+Lz4Ffn4Br09tz+w56z0ymyaHLS8N+xpPHtiNkmiyPPtvjnRgMXWXF1wvtjmLCyclQI4MLtqySY2wXzu0LSpYZ01AQ=="
> /home/ubuntu/.ssh/authorized_keys
RUN chown -R ubuntu:ubuntu /home/ubuntu/.ssh && chmod 600 /home/ubuntu/.ssh/authorized_keys

# Configure SSH server
RUN sed -i 's/#Port 22/Port 22/' /etc/ssh/sshd_config \
    && sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Expose port 22 for SSH
EXPOSE 22

# Allow additional ports to be opened via environment variables (e.g., PORTS="80 443")
ARG PORTS
RUN if [ -n "$PORTS" ]; then for port in $PORTS; do echo "Exposing port $port" && EXPOSE $port; done; fi

# Start SSH service
CMD ["/usr/sbin/sshd", "-D"]
