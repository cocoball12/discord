import discord
from discord.ext import commands
import json
import random
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# 데이터 파일
DATA_FILE = 'economy_data.json'

# 기본 설정
DEFAULT_CONFIG = {
    'fee_rate': 0.05,  # 도박 수수료 (5%)
    'admin_ids': []  # 관리자 ID 목록
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'users': {}, 'config': DEFAULT_CONFIG}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user_balance(data, user_id):
    user_id = str(user_id)
    if user_id not in data['users']:
        data['users'][user_id] = {'balance': 1000, 'last_daily': None}
    return data['users'][user_id]['balance']

def set_user_balance(data, user_id, amount):
    user_id = str(user_id)
    if user_id not in data['users']:
        data['users'][user_id] = {'balance': 0, 'last_daily': None}
    data['users'][user_id]['balance'] = amount

def is_admin(data, user_id):
    return user_id in data['config']['admin_ids']

@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 준비되었습니다!')

@bot.command(name='잔액')
async def balance(ctx):
    """현재 보유 코인 확인"""
    data = load_data()
    balance = get_user_balance(data, ctx.author.id)
    await ctx.send(f'{ctx.author.mention}님의 잔액: **{balance:,}코인**')

@bot.command(name='지급')
async def give_coins(ctx, member: discord.Member, amount: int):
    """다른 유저에게 코인 지급"""
    if amount <= 0:
        await ctx.send('양수만 입력해주세요!')
        return
    
    data = load_data()
    sender_balance = get_user_balance(data, ctx.author.id)
    
    if sender_balance < amount:
        await ctx.send('코인이 부족합니다!')
        return
    
    set_user_balance(data, ctx.author.id, sender_balance - amount)
    receiver_balance = get_user_balance(data, member.id)
    set_user_balance(data, member.id, receiver_balance + amount)
    save_data(data)
    
    await ctx.send(f'{ctx.author.mention}님이 {member.mention}님에게 **{amount:,}코인**을 지급했습니다!')

@bot.command(name='주사위대결')
async def dice_battle(ctx, member: discord.Member, amount: int):
    """주사위 대결 (1-100)"""
    if member.id == ctx.author.id:
        await ctx.send('자기 자신과는 대결할 수 없습니다!')
        return
    
    if amount <= 0:
        await ctx.send('양수만 입력해주세요!')
        return
    
    data = load_data()
    p1_balance = get_user_balance(data, ctx.author.id)
    p2_balance = get_user_balance(data, member.id)
    
    if p1_balance < amount or p2_balance < amount:
        await ctx.send('둘 중 한 명이 코인이 부족합니다!')
        return
    
    # 수수료 계산
    fee = int(amount * data['config']['fee_rate'])
    prize = (amount * 2) - fee
    
    p1_roll = random.randint(1, 100)
    p2_roll = random.randint(1, 100)
    
    embed = discord.Embed(title='🎲 주사위 대결!', color=discord.Color.blue())
    embed.add_field(name=f'{ctx.author.display_name}', value=f'🎲 {p1_roll}', inline=True)
    embed.add_field(name=f'{member.display_name}', value=f'🎲 {p2_roll}', inline=True)
    
    if p1_roll > p2_roll:
        winner = ctx.author
        loser = member
        winner_id = ctx.author.id
        loser_id = member.id
    elif p2_roll > p1_roll:
        winner = member
        loser = ctx.author
        winner_id = member.id
        loser_id = ctx.author.id
    else:
        await ctx.send('무승부! 배팅금이 반환됩니다.')
        return
    
    set_user_balance(data, winner_id, get_user_balance(data, winner_id) + prize - amount)
    set_user_balance(data, loser_id, get_user_balance(data, loser_id) - amount)
    save_data(data)
    
    embed.add_field(name='승자', value=f'🏆 {winner.mention}', inline=False)
    embed.add_field(name='획득', value=f'**{prize:,}코인** (수수료: {fee:,})', inline=False)
    await ctx.send(embed=embed)

@bot.command(name='홀짝')
async def odd_even(ctx, member: discord.Member, amount: int, choice: str):
    """홀짝 게임 (홀/짝 선택)"""
    if member.id == ctx.author.id:
        await ctx.send('자기 자신과는 대결할 수 없습니다!')
        return
    
    if choice not in ['홀', '짝']:
        await ctx.send('홀 또는 짝을 선택해주세요!')
        return
    
    if amount <= 0:
        await ctx.send('양수만 입력해주세요!')
        return
    
    data = load_data()
    p1_balance = get_user_balance(data, ctx.author.id)
    p2_balance = get_user_balance(data, member.id)
    
    if p1_balance < amount or p2_balance < amount:
        await ctx.send('둘 중 한 명이 코인이 부족합니다!')
        return
    
    # 수수료 계산
    fee = int(amount * data['config']['fee_rate'])
    prize = (amount * 2) - fee
    
    p1_roll = random.randint(1, 100)
    p2_roll = random.randint(1, 100)
    total = p1_roll + p2_roll
    result = '홀' if total % 2 == 1 else '짝'
    
    embed = discord.Embed(title='🎲 홀짝 게임!', color=discord.Color.green())
    embed.add_field(name=f'{ctx.author.display_name}', value=f'🎲 {p1_roll}', inline=True)
    embed.add_field(name=f'{member.display_name}', value=f'🎲 {p2_roll}', inline=True)
    embed.add_field(name='합계', value=f'{total} ({result})', inline=False)
    
    if choice == result:
        winner = ctx.author
        winner_id = ctx.author.id
        loser_id = member.id
    else:
        winner = member
        winner_id = member.id
        loser_id = ctx.author.id
    
    set_user_balance(data, winner_id, get_user_balance(data, winner_id) + prize - amount)
    set_user_balance(data, loser_id, get_user_balance(data, loser_id) - amount)
    save_data(data)
    
    embed.add_field(name='승자', value=f'🏆 {winner.mention}', inline=False)
    embed.add_field(name='획득', value=f'**{prize:,}코인** (수수료: {fee:,})', inline=False)
    await ctx.send(embed=embed)

@bot.command(name='뽑기')
async def gacha(ctx):
    """관리자 전용: 랜덤 뽑기 (50-300 배율)"""
    data = load_data()
    
    if not is_admin(data, ctx.author.id):
        await ctx.send('관리자만 사용할 수 있는 명령어입니다!')
        return
    
    # 50-300 범위의 가중치 설정 (높을수록 확률 낮음)
    weights = []
    multipliers = []
    for mult in range(50, 301):
        multipliers.append(mult)
        # 배율이 높을수록 가중치가 낮아짐 (확률 감소)
        weight = 1 / (mult - 49) ** 1.5
        weights.append(weight)
    
    result = random.choices(multipliers, weights=weights)[0]
    
    embed = discord.Embed(title='🎰 랜덤 뽑기!', color=discord.Color.gold())
    embed.add_field(name='결과', value=f'**{result}**', inline=False)
    
    # 등급 표시
    if result >= 250:
        grade = '🌟 전설 등급!'
    elif result >= 200:
        grade = '💎 영웅 등급!'
    elif result >= 150:
        grade = '🔮 희귀 등급'
    elif result >= 100:
        grade = '⚡ 고급 등급'
    else:
        grade = '🔵 일반 등급'
    
    embed.add_field(name='등급', value=grade, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='랭킹')
async def leaderboard(ctx):
    """코인 보유 랭킹"""
    data = load_data()
    
    if not data['users']:
        await ctx.send('아직 등록된 유저가 없습니다!')
        return
    
    sorted_users = sorted(data['users'].items(), key=lambda x: x[1]['balance'], reverse=True)
    
    embed = discord.Embed(title='💰 코인 랭킹', color=discord.Color.purple())
    
    for i, (user_id, user_data) in enumerate(sorted_users[:10], 1):
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.display_name
        except:
            name = f'유저 {user_id}'
        
        medal = ['🥇', '🥈', '🥉'][i-1] if i <= 3 else f'{i}.'
        embed.add_field(
            name=f'{medal} {name}',
            value=f'{user_data["balance"]:,}코인',
            inline=False
        )
    
    await ctx.send(embed=embed)

# 관리자 명령어
@bot.command(name='관리자추가')
@commands.has_permissions(administrator=True)
async def add_admin(ctx, member: discord.Member):
    """관리자 추가 (서버 관리자 권한 필요)"""
    data = load_data()
    if member.id not in data['config']['admin_ids']:
        data['config']['admin_ids'].append(member.id)
        save_data(data)
        await ctx.send(f'{member.mention}님을 관리자로 추가했습니다!')
    else:
        await ctx.send('이미 관리자입니다!')

@bot.command(name='코인추가')
async def add_money(ctx, member: discord.Member, amount: int):
    """관리자: 코인 추가"""
    data = load_data()
    if not is_admin(data, ctx.author.id):
        await ctx.send('관리자만 사용할 수 있는 명령어입니다!')
        return
    
    balance = get_user_balance(data, member.id)
    set_user_balance(data, member.id, balance + amount)
    save_data(data)
    
    await ctx.send(f'{member.mention}님에게 **{amount:,}코인**을 추가했습니다! (현재: {balance + amount:,}코인)')

@bot.command(name='수수료설정')
async def set_fee(ctx, rate: float):
    """관리자: 도박 수수료 설정 (0.0 ~ 1.0)"""
    data = load_data()
    if not is_admin(data, ctx.author.id):
        await ctx.send('관리자만 사용할 수 있는 명령어입니다!')
        return
    
    if rate < 0 or rate > 1:
        await ctx.send('수수료는 0.0 ~ 1.0 사이 값이어야 합니다!')
        return
    
    data['config']['fee_rate'] = rate
    save_data(data)
    
    await ctx.send(f'도박 수수료를 **{rate*100}%**로 설정했습니다!')

@bot.command(name='도움말')
async def help_command(ctx):
    """명령어 목록"""
    embed = discord.Embed(title='📜 명령어 목록', color=discord.Color.blue())
    
    embed.add_field(name='/잔액', value='현재 코인 확인', inline=False)
    embed.add_field(name='/지급 @유저 금액', value='다른 유저에게 코인 지급', inline=False)
    embed.add_field(name='/주사위대결 @유저 금액', value='주사위 대결 (1-100)', inline=False)
    embed.add_field(name='/홀짝 @유저 금액 홀/짝', value='홀짝 게임', inline=False)
    embed.add_field(name='/랭킹', value='코인 랭킹 확인', inline=False)
    embed.add_field(name='--- 관리자 전용 ---', value='‎', inline=False)
    embed.add_field(name='/뽑기', value='랜덤 뽑기 (50-300)', inline=False)
    embed.add_field(name='/관리자추가 @유저', value='관리자 추가', inline=False)
    embed.add_field(name='/코인추가 @유저 금액', value='코인 추가', inline=False)
    embed.add_field(name='/수수료설정 비율', value='도박 수수료 설정 (예: 0.05 = 5%)', inline=False)
    
    await ctx.send(embed=embed)

# 봇 토큰을 여기에 입력하세요
bot.run('YOUR_BOT_TOKEN_HERE')
