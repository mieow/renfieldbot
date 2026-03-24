import discord
from discord.ext import commands
from .logger import log

class AttributeSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)  # Timeout after 60 seconds
        self.selected_attributes = []

    @discord.ui.select(
        placeholder="Select attributes (up to 5)...",
        min_values=1,
        max_values=5,  # Set the maximum number of attributes users can select
        options=[
            discord.SelectOption(label="Willpower", value="willpower", description="Your overall mental resolve"),
            discord.SelectOption(label="Temporary Willpower", value="current_willpower", description="Temporary willpower pool"),
            discord.SelectOption(label="Strength", value="Strength", description="Your physical power"),
            discord.SelectOption(label="Dexterity", value="Dexterity", description="Your agility and coordination"),
            discord.SelectOption(label="Stamina", value="Stamina", description="Your endurance"),
            discord.SelectOption(label="Charisma", value="Charisma", description="Your charm and influence"),
            discord.SelectOption(label="Manipulation", value="Manipulation", description="Your ability to persuade"),
            discord.SelectOption(label="Appearance", value="Appearance", description="Your physical attractiveness"),
            discord.SelectOption(label="Perception", value="Perception", description="Your awareness of surroundings"),
            discord.SelectOption(label="Intelligence", value="Intelligence", description="Your raw mental capacity"),
            discord.SelectOption(label="Wits", value="Wits", description="Your ability to think on your feet"),
            discord.SelectOption(label="Courage", value="Courage", description="Your bravery and resolve"),
            discord.SelectOption(label="Self Control", value="Self Control", description="Your ability to maintain composure"),
            discord.SelectOption(label="Conscience", value="Conscience", description="Your moral sense"),
            discord.SelectOption(label="Initiative", value="init", description="Your ability to act quickly"),
            discord.SelectOption(label="Skip", value="skip", description="Skip this selection"),
        ],
    )
    async def dropdown_callback(self, interaction: discord.Interaction, select: discord.ui.Select, ):
        self.selected_attributes = select.values
        log.info(self.selected_attributes)
        await interaction.response.send_message(
            f"You selected: {', '.join(self.selected_attributes)}", ephemeral=True
        )