# PBT205-A1
ASSIGNMENT 1
Overview: The Chat Prototype is a Python command-line application that uses RabbitMQ to send and receive messages between users.
Tech used: Python, rabbitMQ, Docker, Pika
Features: Connect using a username, specify a chat room when starting the application, send and recieve message, testing with multiple users and rooms.
Prerequisites: Python, Docker desktop installed and running
How to Run: Start Docker Desktop and also ensure RabbitMQ is running. Then, open terminal and start first user : python chat.py Alice general.
Open second terminal and start another user: python chat.py Ayu general. then, tyoe any msg u want and enter. To leave, we can type /quit.
To test: Exchange message in same rooms by different users.
Current status: Command-line prototype is working for basic message exchange. GUI development and further testing still required.
