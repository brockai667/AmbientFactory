# -*- coding: utf-8 -*-
"""Banka money-glitch schem (rucne pisane = logicky sedia, vtipne, ziadne diery).
Kazda schema: id, title (YouTube), steps[]. Krok: cap (titulok), vo (jedna plynula veta),
layout (mascot/icon/icons/two/equation/loop) + params (icon/num/col/eq/a/b/loop).
Ton = sebavedomy 'hack radi ti', ziadny undercut koniec. VO vzdy = 1 veta = 1 karta."""

SCHEMES = [
 {"id":"manufactured-spending","title":"How to make $73,000 a year buying absolutely nothing","steps":[
   {"cap":"Make $73,000 a year.","vo":"Here's how to make seventy three thousand dollars a year.","layout":"mascot"},
   {"cap":"Get a 2% cashback card.","vo":"First, get a credit card that pays you two percent cash back.","layout":"icon","icon":"card","num":"2% back","col":"green"},
   {"cap":"Buy $10,000 in gift cards.","vo":"Use it to buy ten thousand dollars in gift cards.","layout":"icon","icon":"gift","num":"$10,000","col":"red"},
   {"cap":"Turn them into money orders.","vo":"Then turn those gift cards into money orders.","layout":"icon","icon":"order"},
   {"cap":"Deposit them at the bank.","vo":"Deposit the money orders straight into your bank account.","layout":"icon","icon":"cash"},
   {"cap":"Pay off the card.","vo":"And use that exact money to pay off the credit card.","layout":"two","a":"card","b":"cash"},
   {"cap":"$10,000 in a perfect circle.","vo":"You just moved ten thousand dollars in a perfect circle.","layout":"loop","loop":["card","gift","order","cash"]},
   {"cap":"The bank paid you $200.","vo":"And the bank just paid you two hundred dollars to do it.","layout":"icon","icon":"cash","num":"$200","col":"green"},
   {"cap":"Every day = $73,000/yr.","vo":"Do that every single day, and that's seventy three thousand a year.","layout":"icon","icon":"cash","num":"$73,000","col":"green"},
   {"cap":"...for buying nothing.","vo":"For buying absolutely nothing.","layout":"mascot"},
 ]},

 {"id":"copper-pennies","title":"The money glitch hiding in your couch cushions","steps":[
   {"cap":"Your pennies are worth double.","vo":"There's a money glitch hiding in your couch cushions.","layout":"mascot"},
   {"cap":"Get $100 in pennies.","vo":"Go to the bank and ask for a hundred dollars in pennies.","layout":"two","a":"dollar","b":"coin"},
   {"cap":"That's 10,000 coins.","vo":"That gives you ten thousand little copper coins.","layout":"icons","icon":"coin","num":"10,000","col":"ink"},
   {"cap":"The old ones are 95% copper.","vo":"Every penny made before nineteen eighty two is almost pure copper.","layout":"icon","icon":"copper"},
   {"cap":"Each holds 2¢ of copper.","vo":"And the copper inside just one of them is worth about two cents.","layout":"equation","eq":"1¢ coin","num":"= 2¢ copper","col":"green"},
   {"cap":"Your money just doubled.","vo":"So by sorting your pennies, you literally double your money.","layout":"icon","icon":"cash","num":"2x","col":"green"},
   {"cap":"Do it with $10,000.","vo":"Now imagine doing that with ten thousand dollars in pennies.","layout":"icon","icon":"bag","num":"$20,000","col":"green"},
   {"cap":"You're a copper baron.","vo":"Congratulations, you're basically a copper baron.","layout":"mascot"},
 ]},

 {"id":"ewaste-gold","title":"There is $22,000 of gold in a pile of old phones","steps":[
   {"cap":"Old phones are full of gold.","vo":"Here's how to pull twenty two thousand dollars out of old phones.","layout":"mascot"},
   {"cap":"People throw them away.","vo":"Every day, people throw their old broken phones straight in the bin.","layout":"icon","icon":"phone"},
   {"cap":"Collect one ton of them.","vo":"So you collect them, for free, until you have a full ton.","layout":"icons","icon":"phone","num":"1 ton","col":"ink"},
   {"cap":"A ton holds 300g of gold.","vo":"A single ton of phones contains about three hundred grams of real gold.","layout":"icon","icon":"goldbar","num":"300 g","col":"ink"},
   {"cap":"Gold is $75 a gram.","vo":"And gold sells for around seventy five dollars per gram.","layout":"equation","eq":"300g × $75","num":"= $22,500","col":"green"},
   {"cap":"That's $22,500.","vo":"That is twenty two thousand five hundred dollars, from garbage.","layout":"icon","icon":"cash","num":"$22,500","col":"green"},
   {"cap":"From literal trash.","vo":"They call it urban mining, and it's just sitting in landfills.","layout":"loop","loop":["phone","goldbar","cash","bag"]},
   {"cap":"Start collecting.","vo":"So start collecting.","layout":"mascot"},
 ]},

 {"id":"bottle-deposit","title":"How Michigan pays you to collect other people's trash","steps":[
   {"cap":"Trash pays 10¢ in Michigan.","vo":"Here's a glitch that pays you to collect trash.","layout":"mascot"},
   {"cap":"Cans are free everywhere.","vo":"In most states, empty cans are worthless, so people just leave them.","layout":"icons","icon":"can"},
   {"cap":"So you collect them free.","vo":"Which means you can collect as many as you want, for nothing.","layout":"icon","icon":"can"},
   {"cap":"Michigan pays 10¢ each.","vo":"But Michigan pays you ten cents for every single can you bring back.","layout":"icon","icon":"can","num":"10¢","col":"green"},
   {"cap":"Fill a truck.","vo":"So fill a truck with a million free cans.","layout":"icon","icon":"can","num":"1,000,000","col":"ink"},
   {"cap":"That's $100,000.","vo":"That is one hundred thousand dollars in pure profit.","layout":"icon","icon":"cash","num":"$100,000","col":"green"},
   {"cap":"Every single trip.","vo":"And that's every single trip you make.","layout":"loop","loop":["can","cash","bag","can"]},
   {"cap":"Seinfeld did it first.","vo":"Seinfeld did an entire episode about this, so you know it works.","layout":"mascot"},
 ]},

 {"id":"seawater-gold","title":"The ocean is hiding $700 trillion in gold","steps":[
   {"cap":"The ocean is full of gold.","vo":"The ocean is hiding around seven hundred trillion dollars in gold.","layout":"mascot"},
   {"cap":"20 million tons of it.","vo":"There are roughly twenty million tons of gold dissolved in seawater.","layout":"icon","icon":"goldbar","num":"20M tons","col":"ink"},
   {"cap":"And it's completely free.","vo":"Nobody owns it, so all of it is completely free.","layout":"icon","icon":"gem"},
   {"cap":"You just filter the water.","vo":"You just need to filter the gold out of the water.","layout":"icon","icon":"chart"},
   {"cap":"All of it.","vo":"All of the water.","layout":"icon","icon":"gem","num":"$700T","col":"green"},
   {"cap":"That's 1.3 billion km³.","vo":"Which is only about one point three billion cubic kilometers.","layout":"icon","icon":"chart","num":"1.3 bil km³","col":"ink"},
   {"cap":"Grab a bucket.","vo":"So grab a bucket and get started.","layout":"mascot"},
 ]},

 {"id":"penny-doubling","title":"Turn 1 cent into $5 million in a single month","steps":[
   {"cap":"Turn 1¢ into $5,000,000.","vo":"Here's how to turn one cent into five million dollars in a month.","layout":"mascot"},
   {"cap":"Start with a penny.","vo":"You start with a single penny.","layout":"icon","icon":"coin","num":"1¢","col":"ink"},
   {"cap":"Double it every day.","vo":"Then all you do is double it, every single day.","layout":"icon","icon":"coin","num":"×2","col":"green"},
   {"cap":"Day 10: $5.","vo":"By day ten, you already have about five dollars.","layout":"icon","icon":"cash","num":"$5","col":"green"},
   {"cap":"Day 20: $5,000.","vo":"By day twenty, you have over five thousand.","layout":"icon","icon":"cash","num":"$5,000","col":"green"},
   {"cap":"Day 30: $5,000,000.","vo":"And by day thirty, you are sitting on more than five million dollars.","layout":"icon","icon":"bag","num":"$5,000,000","col":"green"},
   {"cap":"It's just math.","vo":"It's not a scam, it's just math.","layout":"chart" if False else "icon","icon":"chart"},
   {"cap":"You only need one thing...","vo":"You just need to find something that reliably doubles your money every day.","layout":"mascot"},
 ]},

 {"id":"casino-martingale","title":"The roulette system where you can never lose","steps":[
   {"cap":"A roulette system that can't lose.","vo":"Here's a roulette system where you literally cannot lose.","layout":"mascot"},
   {"cap":"Bet $1 on red.","vo":"You bet one dollar on red.","layout":"icon","icon":"coin","num":"$1","col":"ink"},
   {"cap":"Lose? Double it.","vo":"If you lose, you simply double your next bet.","layout":"icon","icon":"coin","num":"×2","col":"red"},
   {"cap":"$1, $2, $4, $8, $16...","vo":"One dollar, then two, then four, then eight, then sixteen.","layout":"equation","eq":"1 · 2 · 4 · 8 · 16"},
   {"cap":"Eventually red hits.","vo":"Eventually red comes up, and it always does.","layout":"icon","icon":"chart"},
   {"cap":"You win back everything +$1.","vo":"And when it does, you win back everything you lost, plus one dollar.","layout":"icon","icon":"cash","num":"+$1","col":"green"},
   {"cap":"Repeat 30,000 times.","vo":"Now just repeat that thirty thousand times.","layout":"loop","loop":["coin","chart","cash","bag"]},
   {"cap":"That's $30,000, guaranteed.","vo":"That's thirty thousand dollars, mathematically guaranteed.","layout":"icon","icon":"bag","num":"$30,000","col":"green"},
   {"cap":"Bring infinite money.","vo":"You just need an infinite amount of money to start with.","layout":"mascot"},
 ]},

 {"id":"card-churning","title":"Banks will pay you $7,000 a year to open cards","steps":[
   {"cap":"Banks pay you $7,000/yr.","vo":"Banks will literally pay you seven thousand dollars a year.","layout":"mascot"},
   {"cap":"Open a card with a bonus.","vo":"Open a credit card that gives you a seven hundred dollar signup bonus.","layout":"icon","icon":"card","num":"$700","col":"green"},
   {"cap":"Spend $3,000 on normal stuff.","vo":"You just have to spend three thousand dollars you were already going to spend.","layout":"icon","icon":"cash","num":"$3,000","col":"ink"},
   {"cap":"Collect the $700.","vo":"Then you collect the seven hundred dollar bonus.","layout":"icon","icon":"bag","num":"$700","col":"green"},
   {"cap":"Close it. Open another.","vo":"Now close that card, and open a brand new one.","layout":"two","a":"card","b":"card"},
   {"cap":"Do it 10 times a year.","vo":"Do that about ten times a year.","layout":"loop","loop":["card","cash","bag","card"]},
   {"cap":"That's $7,000 free.","vo":"And that's seven thousand free dollars, every year.","layout":"icon","icon":"cash","num":"$7,000","col":"green"},
   {"cap":"Your credit score disagrees.","vo":"Your credit score is going to have some feelings about this.","layout":"mascot"},
 ]},

 {"id":"retail-arbitrage","title":"How clearance Legos beat the stock market","steps":[
   {"cap":"Legos beat the stock market.","vo":"Retired Lego sets beat the stock market, and here's how you use that.","layout":"mascot"},
   {"cap":"Buy a set on clearance.","vo":"You buy a Lego set on clearance for twenty dollars.","layout":"icon","icon":"gift","num":"$20","col":"red"},
   {"cap":"Never open it.","vo":"Then you do the hardest part, which is never opening it.","layout":"icon","icon":"gift"},
   {"cap":"Lego retires the set.","vo":"A couple years later, Lego stops making that set forever.","layout":"icon","icon":"chart"},
   {"cap":"Now it sells for $60.","vo":"And suddenly your twenty dollar box sells for sixty.","layout":"icon","icon":"cash","num":"$60","col":"green"},
   {"cap":"Buy 500 of them.","vo":"So you buy five hundred of them.","layout":"icons","icon":"gift","num":"×500","col":"ink"},
   {"cap":"That's $20,000 profit.","vo":"And that turns into twenty thousand dollars in profit.","layout":"icon","icon":"bag","num":"$20,000","col":"green"},
   {"cap":"Your closet is full now.","vo":"Your entire closet is plastic bricks now, but you're rich.","layout":"mascot"},
 ]},

 {"id":"vending-machines","title":"How 20 vending machines quietly make $72,000","steps":[
   {"cap":"Vending machines print money.","vo":"A single vending machine quietly prints money while you sleep.","layout":"mascot"},
   {"cap":"One machine = $300/month.","vo":"An average machine makes about three hundred dollars a month.","layout":"icon","icon":"coffee","num":"$300","col":"green"},
   {"cap":"You just refill it.","vo":"All you do is show up sometimes and refill it with snacks.","layout":"icon","icon":"can"},
   {"cap":"Now buy 20 of them.","vo":"So the trick is simply to buy twenty of them.","layout":"icons","icon":"coffee","num":"×20","col":"ink"},
   {"cap":"That's $6,000 a month.","vo":"That's six thousand dollars a month, for refilling snacks.","layout":"icon","icon":"cash","num":"$6,000","col":"green"},
   {"cap":"= $72,000 a year.","vo":"Which comes out to seventy two thousand dollars a year.","layout":"icon","icon":"bag","num":"$72,000","col":"green"},
   {"cap":"Passive-ish income.","vo":"They call it passive income, if you ignore all the driving.","layout":"loop","loop":["coffee","cash","bag","can"]},
   {"cap":"Snack empire acquired.","vo":"Welcome to your snack empire.","layout":"mascot"},
 ]},
]
