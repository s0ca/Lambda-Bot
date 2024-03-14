# Lambda-Bot

Lambda-Bot is a versatile, self-hostable Discord bot designed with flexibility in mind. It employs a modular architecture, allowing for the use of "cogs" or plugins that extend its capabilities. Whether you're looking to play music, take notes, or utilize a variety of other functions, Lambda-Bot has you covered.

## Features

Lambda-Bot comes equipped with a range of features, thanks to its plugin-based system. Some of the available plugins include:

- **Music Player**: Play, pause, skip, and manage music right within your Discord server.
- **Note Taking**: Easily take and organize notes for personal use or within a server channel.
- **And More**: Lambda-Bot is constantly evolving, with new plugins and features being added regularly.

## Prerequisites

Before you can fully utilize Lambda-Bot, make sure you have the following prerequisites installed:

- Python 3.6 or higher
- `sqlite3` - Required for the Note Taking plugin to function properly.

## Installation

To get Lambda-Bot up and running on your server, follow these steps:

1. **Clone the Repository**
```https://github.com/s0ca/Lambda-Bot.git```

2. **Install Dependencies**
Navigate to the cloned repository directory and install the required dependencies:
```pip install -r requirements.txt```

3. **Set Up the Database for Note Taking**
Before you can use the Note Taking plugin, you need to set up a database. Run the `init_db.py` script to create a SQLite3 database:
```python init_db.py```
This script initializes the necessary database structure for storing notes.

4. **Configure the Bot**
Before starting the bot, you need to configure it. Create a `.env` file in the root directory and add your bot's token:

```
BOT_TOKEN=
BOT_OWNER=
DISCORD_GUILD=
ADMIN_ROLE_NAME=
```

5. **Run the Bot**
Finally, start the bot:
```python LambdaBot.py```  


## Adding Plugins

Lambda-Bot's functionality can be easily extended by adding or developing new plugins. To add a plugin, place its file in the `cogs` directory and load it through the bot's configuration.

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

To contribute:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. 

## Support

If you need assistance or have any questions, feel free to open an issue on the GitHub repository.
