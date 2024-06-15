import subprocess

def execute_command(command, args):
    # Define a whitelist of allowed commands
    allowed_commands = ['tree', 'ls', 'find', 'grep', 'awk', 'python', 'du', 'df']

    # Check if the command is in the allowed list
    if command not in allowed_commands:
        return "Command not allowed!"

    # Construct the command to be executed
    full_command = [command] + args

    try:
        # Execute the command and capture output
        result = subprocess.run(full_command, text=True, capture_output=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        # Return error message if command fails
        return f"An error occurred: {e.stderr}"
    except Exception as e:
        # Generic exception handling
        return f"An error occurred: {str(e)}"


