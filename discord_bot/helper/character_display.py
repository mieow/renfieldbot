CIRCLE_FULL = '⚪'
CIRCLE_EMPTY = '⚫'

def get_padding(text, max_length):
	"""Adds spaces to the text until it reaches the max length."""
	return text + " " * (max_length - len(text))

def displayCharacter(data):
	padding = "   "
	# Start with basic information
	message = (
		f"**Character Name:** {data['name']}{padding}"
		f"**Sect:** {data['sect']}{padding}"
		f"**Clan:** {data['clan']}\n"
		f"{padding}**Domain:** {data['domain']}{padding}"
		f"**Generation:** {data['generation']}\n"
		f"{padding}**Bloodpool:** {data['bloodpool']}{padding}"
		f"**Willpower:** {data['willpower']}\n"
		f"**Path of Enlightenment:** {data['path_of_enlightenment']}\n\n"
	)


	message += "## Attributes:\n"
	message += displayAttributes(data)
	message += "\n## Abilities:\n"
	message += displayAbilities(data)



	# Add disciplines
	message += "\n**Disciplines:**\n"
	for discipline in data.get("disciplines", []):
		message += f"{padding}{discipline['name']}: {discipline['level']}\n"

	return message

def displayAbilities(data):
	abilities = data.get("abilities", [])

	if abilities:
		message = "```"

		# Group abilities programmatically by their grouping
		grouped_abilities = {"Knowledges": [], "Skills": [], "Talents": []}
		for ability in abilities:
			grouping = ability.get("grouping", "Ungrouped")
			if grouping in grouped_abilities:
				grouped_abilities[grouping].append(ability)

		# Determine padding for neat alignment
		max_skillname_length = max(len(ability["skillname"]) for ability in abilities)
		max_level_length = max(len(str(ability["level"])) for ability in abilities)

		# Display abilities in three columns: Knowledges, Skills, Talents
		message += f"Knowledges{' ' * (max_skillname_length + max_level_length + 11 - len('Knowledges'))}| Skills{' ' * (max_skillname_length + max_level_length + 11 - len('Skills'))}| Talents{' ' * (max_skillname_length + max_level_length + 11 - len('Talents'))}\n"
		
		# Get the max row count for all groups
		max_rows = max(len(group) for group in grouped_abilities.values())

		for row_idx in range(max_rows):
			row = []
			
			# For each column (Knowledges, Skills, Talents), get the corresponding ability
			for group in ["Knowledges", "Skills", "Talents"]:
				abilities_in_group = grouped_abilities[group]
				if row_idx < len(abilities_in_group):
					ability = abilities_in_group[row_idx]
					skill_name = ability["skillname"].ljust(max_skillname_length)
					level = str(ability["level"]).rjust(max_level_length)
					row.append(f"{skill_name} (Level: {level})")
				else:
					row.append(" " * (max_skillname_length + max_level_length + 10))  # Add padding for empty columns

			# Join the row elements with spacing for columns
			message += " | ".join(row) + "\n"

		message += "```"
		return message

	else:
		return "No abilities to display."
	
	
def displayAttributes(characterInfo):
	attributes = characterInfo.get("attributes", [])
	attributes = attributes[0:9]  # Limit to the first 9 attributes

	if isinstance(attributes, list):
		message = "```"

		# Group attributes into Physical, Social, and Mental categories
		categories = {
			"Physical": ["Strength", "Dexterity", "Stamina"],
			"Social": ["Charisma", "Manipulation", "Appearance"],
			"Mental": ["Intelligence", "Wits", "Perception"],
		}

		# Create a mapping of attribute names to their levels
		attribute_levels = {attr["name"]: attr["level"] for attr in attributes if isinstance(attr, dict)}

		# Calculate padding for neat alignment
		max_category_length = max(len(category) for category in categories.keys())
		max_attribute_length = max(len(attr[0:3]) for attr in sum(categories.values(), []))
		max_level_length = max(len(str(attribute_levels.get(attr, ""))) for attr in sum(categories.values(), []))

		# Format the header row
		header_row = " | ".join(category.ljust(max_category_length) for category in categories.keys())
		message += f"{header_row}\n"
		message += f"{'-' * len(header_row)}\n"

		# Display attributes under their categories
		for i in range(3):  # Assuming there are 3 attributes per category
			row = []
			for category in categories.keys():
				attr_name = categories[category][i]
				attr_level = attribute_levels.get(attr_name, "-")
				row.append(f"{attr_name[0:3]}: {str(attr_level).rjust(max_level_length)}".ljust(max_attribute_length + max_level_length + 2))
			message += f"{(len(category) - 3) * " "}| ".join(row) + "\n"

		message += "```"
		return message
	else:
		return "Invalid attributes format."





def get_bloodpool_max(generation):
	for row in generation_bloodpool:
		if row["generation"] == generation:
			return row["bloodpool_max"]
	return 10  # If generation error, assume generation 13

generation_bloodpool = [
	{"generation": 13, "bloodpool_max": 10},
	{"generation": 12, "bloodpool_max": 11},
	{"generation": 11, "bloodpool_max": 12},
	{"generation": 10, "bloodpool_max": 13},
	{"generation": 9, "bloodpool_max": 14},
	{"generation": 8, "bloodpool_max": 15},
	{"generation": 7, "bloodpool_max": 20},
	{"generation": 6, "bloodpool_max": 30},
	{"generation": 5, "bloodpool_max": 40},
]
