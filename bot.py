import discord
import subprocess
from dotenv import load_dotenv
import os
import threading
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from discord.ext import tasks
from discord.ext import commands
import asyncio
intents = discord.Intents.default()
intents.members = True 
intents.message_content=True

sched = BackgroundScheduler()
sched.start()
load_dotenv()
TOKEN=os.getenv('DISCORD_TOKEN')
GUILD=os.getenv('GUILD')
client=commands.Bot(command_prefix="track",intents=intents,strip_after_prefix=True,owner_id=int(os.getenv("ME")))
discord.utils.setup_logging()

@client.event
async def on_ready():
    global CHANNEL
    CHANNEL=int(os.getenv('CHANNEL'))
    CHANNEL=await client.fetch_channel(CHANNEL)
    await CHANNEL.send('Hello! Script is Running!')
    in_sec=int(os.getenv('DELAY'))*60*60                        
    print(in_sec)
    out.start()
    chec=sched.add_job(execute,'interval', seconds = in_sec)        
    chec2=sched.add_job(takeover,'interval',seconds= in_sec)
    await client.load_extension("jishaku")
@client.event
async def on_message(message:discord.Message):
    if message.author == client.user or message.author.bot:      #Ignore messages by bot itself
        return
    await client.process_commands(message)
    
@client.group(name='add',help='Add a domain or command to the list')
async def add(ctx:commands.Context):
    if ctx.invoked_subcommand is None:
        return await ctx.send("Please use either `track add domain` or `track add command`")
@add.command(name='domain')
async def add_domain(ctx:commands.Context,*,domain:str):
    domain_file=open("./tmp/domains_list","a+")
    domain_file.write(domain+'\n')
    await ctx.send("Domain added!")
    domain_file.close()
@add.command(name='command')
async def add_command(ctx:commands.Context,*,command:str):
    command_file=open("./tmp/commands_list","a+")
    command_file.write(command+'\n')
    await ctx.send("Added!")
    command_file.close()			  

@client.group(name='rm',aliases=['remove'],help='Remove a command or domain from the list')
async def remove(ctx:commands.Context):
    if ctx.invoked_subcommand is None:
        return await ctx.send("Please use either `track rm domain` or `track rm command`")
@remove.command(name='domain')
async def remove_domain(ctx:commands.Context,*,domain:str):
    with open("./tmp/domains_list","r+") as file:
        lines=file.readlines()
        if (domain+"\n") in lines:
            lines.remove(domain+"\n")
            file.truncate()
            file.writelines(lines)
        else:
            return await ctx.send(f"Could not find {domain} in the list of domains!")
@remove.command(name='command')
async def remove_command(ctx:commands.Context,*,command:str):
    with open("./tmp/commands_list","r+") as file:
        lines=file.readlines()
        if (command+"\n") in lines:
            lines.remove(command+"\n")
            file.truncate()
            file.writelines(lines)
        else:
            return await ctx.send(f"Could not find {command} in the list of commands!")
        
        

@tasks.loop(hours=12)
async def out():  
    print("Inside out1")                  
    data=check("new")
    if(data):
        await CHANNEL.send("New Subdomain/s Found")
        await CHANNEL.send('\n'.join([l.strip() for l in data]))
    print("Inside out2")
    data=check("to")
    if(data):
        await CHANNEL.send("Subdomain Takeover Vulnerable Domain Found")
        await CHANNEL.send('\n'.join([l.strip() for l in data])) 

def execute():
    print("Inside execute")
    commands=open("./tmp/commands_list","r+")   
    domains=open("./tmp/domains_list","r+")
    lines=commands.readlines()
    counter=0
    for line in lines:
        counter+=1
        command=line.strip()
        threads=[]
        lines2=domains.readlines()
        for l in lines2:
            domain=l.strip()
            t=threading.Thread(target=run, args=(command,domain,counter,))
            threads.append(t)
            t.start()
        for x in threads:
            x.join()
        domains.seek(0)
    commands.close()
    domains.close() 

def run(what,where,flag):
    print("Inside run")
    cmd=what+" "+where+" > ./tmp/"+where+"_sub.txt" 
    cmd2=what+" "+where+" >> ./tmp/"+where+"_sub.txt"                              
    print(cmd)
    if(flag == 1):
        process = subprocess.Popen(cmd, shell=True)
        process.wait()
    else:
        process = subprocess.Popen(cmd2, shell=True)
        process.wait()
       
def check(con):
    print("Inside check")  
    data=[]                                              
    if(con=="new"):
        print("debug")
        if(os.path.isfile("./tmp/domains_list")):
            sites=open("./tmp/domains_list","r+")
            sites_lines=sites.readlines()
            loc="./tmp/"
            for a in sites_lines:
                fname=a.strip()+"_sub.txt"
                f2name="."+fname
                subprocess.Popen("touch "+loc+"changes",shell=True).wait()
                if(os.path.isfile(loc+f2name)):
                    subprocess.Popen("diff "+loc+fname+" "+loc+f2name+" | grep '<' | sed 's/^< //g' > ./tmp/changes",shell=True).wait()          
                    subprocess.Popen("cp "+loc+fname+" "+loc+f2name,shell=True).wait()
                else:
                    subprocess.Popen("cp "+loc+fname+" "+loc+f2name,shell=True).wait()
                if(os.stat(loc+"changes").st_size != 0):
                    f=open("./tmp/changes","r")
                    data=f.readlines()
                    f.close()
                    subprocess.Popen("rm ./tmp/changes",shell=True).wait()                                                       
            sites.close()
    if(con=="to"):
        if(os.path.isfile("./tmp/takeover")):
            if(os.stat("./tmp/takeover").st_size != 0):
                file1=open("./tmp/takeover","r")
                data=file1.readlines()
                file1.close()
                subprocess.Popen("rm ./tmp/takeover",shell=True).wait()
    return data

def takeover():
    print("Inside takeover")
    dom=open("./tmp/domains_list","r")
    lines=dom.readlines()
    for l in lines:
        b=l.strip()
        subprocess.Popen("subjack -w ./tmp/"+b+"_sub.txt >> ./tmp/takover",shell=True)
    dom.close()
           
asyncio.run(client.start(TOKEN))
