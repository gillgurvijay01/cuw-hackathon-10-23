# Installind dependencies 
from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
# Loading the .env file
load_dotenv()
KEY = os.getenv("DISCORD_API_KEY")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

def get_current_status():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    working = []
    on_break = []
    
    for user_id, data in attendance_data.items():
        # Skip users who have checked out
        if 'out_time' in data:
            continue
            
        if 'in_time' in data:
            user = bot.get_user(int(user_id))
            if user:
                time_in = data['in_time']
                hours, minutes = format_time_difference(time_in, current_time)
                
                if data.get('on_break'):
                    break_start = data['on_break']
                    break_hours, break_minutes = format_time_difference(break_start, current_time)
                    on_break.append({
                        'name': user.name,
                        'break_duration': f"{int(break_hours)}h {int(break_minutes)}m"
                    })
                else:
                    working.append({
                        'name': user.name,
                        'duration': f"{int(hours)}h {int(minutes)}m"
                    })
    
    return working, on_break


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')    

# Initialize bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store user attendance data
attendance_data = {}

# Load existing data if available
def load_data():
    if os.path.exists('attendance.json'):
        with open('attendance.json', 'r') as f:
            return json.load(f)
    return {}

# Save data to file
def save_data():
    with open('attendance.json', 'w') as f:
        json.dump(attendance_data, f)

# Calculate time difference in hours and minutes
def format_time_difference(start_time, end_time):
    diff = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    hours = diff.total_seconds() / 3600
    minutes = (diff.total_seconds() % 3600) / 60
    return hours, minutes

@bot.event
async def on_ready():
    global attendance_data
    attendance_data = load_data()
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name='checkin')  # Changed from 'in_' to 'checkin' to be more clear
async def checkin(ctx):
    user_id = str(ctx.author.id)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if user_id in attendance_data and 'in_time' in attendance_data[user_id] and 'out_time' not in attendance_data[user_id]:
        await ctx.send("You're already clocked in!")
        return
    
    attendance_data[user_id] = {
        'in_time': current_time,
        'breaks': [],
        'total_break_time': 0
    }
    save_data()
    
    embed = discord.Embed(
        title="Clock In",
        description=f"Successfully clocked in!",
        color=discord.Color.green()
    )
    embed.add_field(name="Time", value=current_time, inline=False)
    embed.set_footer(text=f"User: {ctx.author.name}")
    
    await ctx.send(embed=embed)

@bot.command(name='startbreak')  # Changed from 'break_' to 'startbreak'
async def startbreak(ctx):
    user_id = str(ctx.author.id)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if user_id not in attendance_data or 'in_time' not in attendance_data[user_id]:
        await ctx.send("You haven't clocked in yet!")
        return
    
    if attendance_data[user_id].get('on_break'):
        await ctx.send("You're already on break!")
        return
    
    # Calculate time worked so far
    last_time = attendance_data[user_id].get('break_return_time', attendance_data[user_id]['in_time'])
    hours, minutes = format_time_difference(last_time, current_time)
    
    attendance_data[user_id]['on_break'] = current_time
    save_data()
    
    embed = discord.Embed(
        title="Break Started",
        description=f"Your break has started",
        color=discord.Color.blue()
    )
    embed.add_field(name="Break Start Time", value=current_time, inline=False)
    embed.add_field(name="Time Worked So Far", value=f"{int(hours)}h {int(minutes)}m", inline=False)
    embed.set_footer(text=f"User: {ctx.author.name}")
    
    await ctx.send(embed=embed)

@bot.command()
async def back(ctx):
    user_id = str(ctx.author.id)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if user_id not in attendance_data or 'in_time' not in attendance_data[user_id]:
        await ctx.send("You haven't clocked in yet!")
        return
    
    if not attendance_data[user_id].get('on_break'):
        await ctx.send("You weren't on break!")
        return
    
    # Calculate break duration
    break_start = attendance_data[user_id]['on_break']
    break_hours, break_minutes = format_time_difference(break_start, current_time)
    
    # Update break information
    attendance_data[user_id]['breaks'].append({
        'start': break_start,
        'end': current_time,
        'duration': break_hours * 60 + break_minutes
    })
    attendance_data[user_id]['total_break_time'] += break_hours * 60 + break_minutes
    attendance_data[user_id]['break_return_time'] = current_time
    del attendance_data[user_id]['on_break']
    
    # Calculate remaining time in 8-hour shift
    total_worked_hours, total_worked_minutes = format_time_difference(
        attendance_data[user_id]['in_time'],
        current_time
    )
    total_worked_minutes = total_worked_hours * 60 + total_worked_minutes - attendance_data[user_id]['total_break_time']
    remaining_minutes = 480 - total_worked_minutes  # 480 minutes = 8 hours
    
    save_data()
    
    embed = discord.Embed(
        title="Back from Break",
        description="Welcome back!",
        color=discord.Color.green()
    )
    embed.add_field(name="Break Duration", value=f"{int(break_hours)}h {int(break_minutes)}m", inline=False)
    embed.add_field(name="Remaining Time for 8-hour shift", value=f"{int(remaining_minutes/60)}h {int(remaining_minutes%60)}m", inline=False)
    embed.set_footer(text=f"User: {ctx.author.name}")
    
    await ctx.send(embed=embed)

@bot.command()
async def checkout(ctx):  # Changed from 'out' to 'checkout'
    user_id = str(ctx.author.id)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if user_id not in attendance_data or 'in_time' not in attendance_data[user_id]:
        await ctx.send("You haven't clocked in yet!")
        return
    
    if attendance_data[user_id].get('on_break'):
        await ctx.send("Please return from break first!")
        return
    
    # Calculate total time
    total_hours, total_minutes = format_time_difference(
        attendance_data[user_id]['in_time'],
        current_time
    )
    
    # Calculate on-desk time (total time - break time)
    total_minutes = total_hours * 60 + total_minutes
    on_desk_minutes = total_minutes - attendance_data[user_id]['total_break_time']
    on_desk_hours = on_desk_minutes // 60
    on_desk_minutes_remainder = on_desk_minutes % 60
    
    # Calculate break statistics
    num_breaks = len(attendance_data[user_id]['breaks'])
    avg_break_duration = attendance_data[user_id]['total_break_time'] / num_breaks if num_breaks > 0 else 0
    
    # Check if 8 hours completed
    remaining_minutes = 480 - on_desk_minutes  # 480 minutes = 8 hours
    
    embed = discord.Embed(
        title="Clock Out Summary",
        description=f"Clock out time: {current_time}",
        color=discord.Color.red()
    )
    embed.add_field(name="Total Time in Office", value=f"{int(total_hours)}h {int(total_minutes%60)}m", inline=False)
    embed.add_field(name="On-desk Time", value=f"{int(on_desk_hours)}h {int(on_desk_minutes_remainder)}m", inline=False)
    embed.add_field(name="Total Breaks Taken", value=str(num_breaks), inline=True)
    embed.add_field(name="Average Break Duration", value=f"{int(avg_break_duration)} minutes", inline=True)
    
    if remaining_minutes > 0:
        embed.add_field(
            name="Remaining Time", 
            value=f"You need to work {int(remaining_minutes/60)}h {int(remaining_minutes%60)}m more to complete 8 hours",
            inline=False
        )
    
    embed.set_footer(text=f"User: {ctx.author.name}")
    
    attendance_data[user_id]['out_time'] = current_time
    save_data()
    
    await ctx.send(embed=embed)
@bot.command(name='mystatus')
async def mystatus(ctx):
    """Show detailed status for the requesting user"""
    user_id = str(ctx.author.id)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if user_id not in attendance_data:
        await ctx.send("You haven't clocked in today!")
        return
    
    data = attendance_data[user_id]
    embed = discord.Embed(
        title="Your Current Status",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    # Calculate time since clock in
    hours, minutes = format_time_difference(data['in_time'], current_time)
    embed.add_field(name="Clocked In At", value=data['in_time'], inline=False)
    embed.add_field(name="Total Time", value=f"{int(hours)}h {int(minutes)}m", inline=True)
    
    # Break information
    if data.get('on_break'):
        break_hours, break_minutes = format_time_difference(data['on_break'], current_time)
        embed.add_field(name="Current Break Duration", value=f"{int(break_hours)}h {int(break_minutes)}m", inline=True)
        embed.add_field(name="Status", value="On Break ☕", inline=False)
    else:
        embed.add_field(name="Status", value="Working 👨‍💻", inline=False)
    
    # Break statistics
    total_breaks = len(data['breaks'])
    embed.add_field(name="Total Breaks Today", value=str(total_breaks), inline=True)
    embed.add_field(name="Total Break Time", value=f"{int(data['total_break_time'])} minutes", inline=True)
    
    await ctx.send(embed=embed)

# New status commands
@bot.command(name='status')
async def status(ctx):
    """Show current status of all team members"""
    working, on_break = get_current_status()
    
    embed = discord.Embed(
        title="Team Status Overview",
        description="Current status of all team members",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    # Add working members to embed
    working_text = "\n".join([f"👨‍💻 {w['name']} - Working for {w['duration']}" for w in working]) if working else "No one is currently working"
    embed.add_field(name=f"Working ({len(working)})", value=working_text, inline=False)
    
    # Add members on break to embed
    break_text = "\n".join([f"☕ {b['name']} - On break for {b['break_duration']}" for b in on_break]) if on_break else "No one is currently on break"
    embed.add_field(name=f"On Break ({len(on_break)})", value=break_text, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='working')
async def working(ctx):
    """Show only team members currently working"""
    working, _ = get_current_status()
    
    embed = discord.Embed(
        title="Currently Working",
        description="Team members currently working",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    
    if working:
        for worker in working:
            embed.add_field(
                name=worker['name'],
                value=f"Duration: {worker['duration']}",
                inline=True
            )
    else:
        embed.description = "No team members are currently working"
    
    await ctx.send(embed=embed)

@bot.command(name='onbreak')
async def onbreak(ctx):
    """Show only team members currently on break"""
    _, on_break = get_current_status()
    
    embed = discord.Embed(
        title="Currently On Break",
        description="Team members currently on break",
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    
    if on_break:
        for breaker in on_break:
            embed.add_field(
                name=breaker['name'],
                value=f"Break duration: {breaker['break_duration']}",
                inline=True
            )
    else:
        embed.description = "No team members are currently on break"
    
    await ctx.send(embed=embed)

bot.run(KEY)

print("Hola")
