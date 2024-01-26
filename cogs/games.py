import random
import asyncio
from discord.ext import commands

class Games(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.cardValues = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'K', 'Q']
        self.nipes = ['Hearts', 'Diamonds', 'Clubs', 'Spades']

    def createDeck(self):
        newDeck = []
        for value in self.cardValues:
            for nipe in self.nipes:
                newDeck.append({'nipe': nipe, 'value': value})
        return newDeck
    
    def handValue(self, hand):
        handvalue = 0
        aces = 0
        for card in hand:
            if card['value'] == 'J' or card['value'] == 'K' or card['value'] == 'Q':
                handvalue += 10
            elif card['value'] == 'A':
                    handvalue += 11
                    aces += 1
            else:
                handvalue += int(card['value'])

        while aces:
            if handvalue > 21:
                handvalue -= 10
                aces -= 1
            else:
                break

        return handvalue
    
    @commands.command(name="blackjack", pass_context=True)
    async def blackjack(self, ctx):
        state = "play"
        deck = self.createDeck()

        botHand = [deck.pop(random.randrange(0, len(deck))), deck.pop(random.randrange(0, len(deck)))]
        playerHand = [deck.pop(random.randrange(0, len(deck))), deck.pop(random.randrange(0, len(deck)))]

        while state == "play":
            await ctx.send("**My hand:**\n" +
                f"{botHand[0]['value']} of {botHand[0]['nipe']}\n" + "...\n" + 
                "---------------------------------------")

            await ctx.send("**Your hand:**\n" +
            "\n".join([f"{card['value']} of {card['nipe']}" for card in playerHand]))

            if (self.handValue(playerHand) > 21):
                await ctx.send("**You blew up!**")
                await ctx.send("**Shikinami wins!**")
                return

            message = await ctx.send("(🔼 to ask for more, ⏹️ to stay.)\n" + "**React to this message with your play.**")
            await message.add_reaction('🔼')
            await message.add_reaction('⏹️')
            await ctx.send("-----------------------------------------------------------------")

            def checkPlay(reaction, user):
                nonlocal state
                if (ctx.author == user):
                    if (reaction.emoji == '🔼'):
                        state = 'play'
                        return True
                    elif reaction.emoji == '⏹️':
                        state = 'stop'
                        return True
                return False

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=checkPlay)
            except asyncio.TimeoutError:
                await ctx.send("**You took too long. Game over**")
                return

            if state == "play":
                playerHand.append(deck.pop(random.randrange(0, len(deck))))

        while self.handValue(botHand) <= 18:
            botHand.append(deck.pop(random.randrange(0, len(deck))))

        await ctx.send("**My hand:**\n" + 
            "\n".join([f"{card['value']} of {card['nipe']}" for card in botHand]) + "\n" +
            f"**Valued at {self.handValue(botHand)}**\n" +
            "---------------------------------------")
        await ctx.send("**Your hand:**\n" +
            "\n".join([f"{card['value']} of {card['nipe']}" for card in playerHand]) + "\n" +
            f"**Valued at {self.handValue(playerHand)}**")

        if self.handValue(playerHand) < self.handValue(botHand) and self.handValue(botHand) < 22:
            await ctx.send(f"**Shikinami is the winner!**")
        elif self.handValue(playerHand) == self.handValue(botHand):
            await ctx.send("**Game tied!**")
        else: 
            await ctx.send(f"**{ctx.message.author.display_name} is the winner!**")

async def setup(bot):
    await bot.add_cog(Games(bot))

