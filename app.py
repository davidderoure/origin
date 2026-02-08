# app.py - Flask web server for Story Recommender Demo

from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import json
import os

# Import your recommender system
from rec2 import StoryRecommender, AnalyticsEvent, MoodScore

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Initialize recommender with sample stories
recommender = StoryRecommender(
    event_half_life_days=30.0,
    mood_half_life_days=14.0,
    transition_window_minutes=1440.0
)

# Add sample stories
def initialize_stories():
    # Ancient artifacts (6 stories)
    recommender.add_story("story1", "The Alfred Jewel", "ancient", 
                         ["mysterious", "royal", "craftsmanship"])
    recommender.add_story("story4", "The Scorpion Macehead", "ancient", 
                         ["Egyptian", "powerful", "discovery"])
    recommender.add_story("story8", "The Parian Marble", "ancient", 
                         ["chronological", "scholarly", "timeless"])
    recommender.add_story("story11", "The Minoan Snake Goddess", "ancient", 
                         ["mystical", "feminine", "ritual"])
    recommender.add_story("story12", "The Roman Mosaic", "ancient", 
                         ["artistic", "domestic", "preserved"])
    recommender.add_story("story13", "The Ure Greek Vase", "ancient", 
                         ["athletic", "celebration", "beauty"])
    
    # Natural history (4 stories)
    recommender.add_story("story2", "The Last Dodo", "natural", 
                         ["extinct", "haunting", "loss"])
    recommender.add_story("story7", "Tradescant's Ark", "natural", 
                         ["curious", "wondrous", "collection"])
    recommender.add_story("story14", "The Ichthyosaur", "natural", 
                         ["prehistoric", "marine", "fossilized"])
    recommender.add_story("story15", "The Giant Irish Deer", "natural", 
                         ["magnificent", "ice-age", "extinct"])
    
    # Medieval (4 stories)
    recommender.add_story("story3", "Guy Fawkes' Lantern", "medieval", 
                         ["conspiracy", "history", "rebellion"])
    recommender.add_story("story6", "The Abingdon Sword", "medieval", 
                         ["warrior", "crafted", "legendary"])
    recommender.add_story("story16", "The Illuminated Manuscript", "medieval", 
                         ["sacred", "illustrated", "devotional"])
    recommender.add_story("story17", "The Lewis Chessmen", "medieval", 
                         ["carved", "strategic", "mysterious"])
    
    # Cultural (4 stories)
    recommender.add_story("story5", "Powhatan's Mantle", "cultural", 
                         ["ceremonial", "heritage", "connection"])
    recommender.add_story("story9", "Ceremonial Axes", "cultural", 
                         ["ritual", "spiritual", "ancestral"])
    recommender.add_story("story18", "The Shrunken Heads", "cultural", 
                         ["transformative", "warrior", "ritual"])
    recommender.add_story("story19", "The Samurai Armor", "cultural", 
                         ["honor", "protective", "disciplined"])
    
    # Scientific (3 stories)
    recommender.add_story("story10", "Einstein's Blackboard", "scientific", 
                         ["genius", "lecture", "revelation"])
    recommender.add_story("story20", "The Astrolabe", "scientific", 
                         ["navigational", "astronomical", "precise"])
    recommender.add_story("story21", "Carroll's Camera", "scientific", 
                         ["photographic", "innovative", "capturing"])
    
    # Artistic (3 stories)
    recommender.add_story("story22", "The Light of the World", "artistic", 
                         ["symbolic", "glowing", "spiritual"])
    recommender.add_story("story23", "Michelangelo's Drawing", "artistic", 
                         ["masterful", "anatomical", "renaissance"])
    recommender.add_story("story24", "Islamic Ceramic Bowl", "artistic", 
                         ["geometric", "calligraphic", "luminous"])
    
    # Literary (1 story)
    recommender.add_story("story25", "Shakespeare's First Folio", "literary", 
                         ["dramatic", "immortal", "eloquent"])

initialize_stories()

# Story content (for demo purposes)
STORY_CONTENT = {
    "story1": """
        In the Ashmolean Museum, behind glass that has protected it for centuries, 
        lies the Alfred Jewel—a masterpiece of Anglo-Saxon craftsmanship. Barely 
        larger than a thumb, this golden artifact bears the inscription "AELFRED MEC 
        HEHT GEWYRCAN"—Alfred ordered me to be made.
        
        King Alfred the Great commissioned this jewel over a thousand years ago, perhaps 
        as a pointer for reading sacred texts. The enamel figure gazes out with knowing 
        eyes, holding flowering rods, forever frozen in a moment of medieval artistry. 
        Gold, enamel, and rock crystal—materials that would outlast kingdoms.
        
        Discovered in 1693 in a Somerset field, the jewel had waited centuries in the 
        earth. What stories could it tell? Of the king who held it, of the craftsman 
        who shaped it, of the battles and books and prayers it witnessed. In your 
        reflection in its glass case, you become part of its endless story—another 
        pair of eyes that has beheld its beauty, another moment in its long existence.
    """,
    
    "story2": """
        The Oxford Dodo stands in the Museum of Natural History, the most famous 
        extinct bird in the world. Unlike the complete skeletons elsewhere, this is 
        something more poignant—the only soft tissue remains of a dodo anywhere. 
        A head and a foot, dried and preserved, the last physical remnants of a 
        species that vanished from Earth in the 1660s.
        
        These fragments once belonged to the Tradescant collection, displayed as a 
        curiosity when dodos still lived on Mauritius. The museum's founder almost 
        had the deteriorating specimen destroyed, but an assistant saved the head and 
        foot—the only reason we can see real dodo tissue today. Every other dodo is 
        bones, or paintings, or descriptions.
        
        Standing before this display, you're looking at absence made visible. The dodo 
        became extinct before science understood extinction was possible. This bird's 
        remnants ask a question that echoes across centuries: What are we losing now 
        that we don't yet realize we should save? The dodo watches with its preserved 
        eye, a witness to its own species' ending, a warning written in feathers and bone.
    """,
    
    "story3": """
        In the Ashmolean Museum rests an unassuming lantern—metal, practical, 
        unremarkable except for one detail: it was carried by Guy Fawkes on the night 
        of November 5th, 1605, when he was discovered in the cellars beneath Parliament, 
        guarding thirty-six barrels of gunpowder.
        
        Imagine the flickering flame inside this lantern, casting shadows on stone walls, 
        illuminating the face of a man who believed he was about to change history with 
        fire. The Gunpowder Plot failed, of course. Fawkes was arrested, tortured, and 
        executed. But his lantern survived.
        
        For over four hundred years, this simple light-bearer has endured. It witnessed 
        the night when England's entire government nearly vanished in an explosion. It 
        was there in the darkness of conspiracy, in the moment of discovery, in the 
        instant when rebellion became capture. Every November 5th, when bonfires light 
        the British sky, this lantern sits quiet in its case—the authentic flame that 
        nearly ignited revolution, now cold, now still, now only light in memory.
    """,
    
    "story4": """
        The Scorpion Macehead sits among Egyptian treasures in the Ashmolean, carved 
        from limestone over 5,000 years ago. It depicts a king—possibly named Scorpion, 
        or perhaps the scorpion is merely a symbol—performing a ceremonial act: cutting 
        an irrigation canal, bringing water and life to the land.
        
        This was made before the pyramids, before hieroglyphic writing was fully 
        developed, in an Egypt that was still becoming Egypt. The carving shows 
        attendants, standards, birds—a snapshot of a world that existed fifty centuries 
        before Instagram, yet the artist's skill still speaks clearly across that 
        impossible gulf of time.
        
        Look closely at the scorpion symbol above the king's head. Scholars debate who 
        this ruler was, whether he united Upper Egypt, whether he was the same king 
        depicted on the Narmer Palette. But the mystery makes it more powerful. This 
        stone has outlasted certainty itself. Empires rose and fell, languages were 
        born and died, and still this macehead endures—a king without a name, a story 
        without an ending, a moment carved in stone when the world was young.
    """,
    
    "story5": """
        Hanging in the Ashmolean is a deerskin mantle embroidered with shells, forming 
        patterns of a human figure flanked by animals. This is Powhatan's Mantle—or 
        rather, it might be. The cloak belonged to the Powhatan people of Virginia, 
        possibly to Chief Powhatan himself, father of Pocahontas, who met the Jamestown 
        colonists in 1607.
        
        The shells tell a story in their arrangement—a cosmology, a map of power, a 
        world-view sewn into hide. Each shell was carefully selected, pierced, and 
        attached. The labor represents not just hours but meaning, not just craft but 
        culture. This was wealth and authority made visible, made wearable.
        
        The mantle arrived in England in the 1630s, part of John Tradescant's collection 
        of "rarities and curiosities." But it's not a curiosity—it's a voice. In an era 
        when Indigenous peoples were being pushed from their lands, this mantle survived, 
        carrying its maker's vision across the ocean, across centuries. Stand before it 
        and you're not looking at an artifact. You're receiving a message from a world 
        that refused to be forgotten, embroidered with shells that shine like stars, 
        telling stories that shine like truth.
    """,
    
    "story6": """
        The Abingdon Sword lies in its case, pattern-welded steel from the seventh 
        century, discovered in a Saxon cemetery. The blade shows the technique of 
        combining iron and steel, twisted and forged, creating both strength and beauty—
        the swirling patterns visible even now, like water frozen in metal.
        
        This sword was made for a warrior of status, buried with them for the journey 
        beyond death. The Anglo-Saxon world believed a good sword had a spirit, a 
        personality. Beowulf spoke of swords by name. This blade likely had a name too, 
        now lost to time, whispered by voices speaking a language that evolved into 
        English but would sound alien to modern ears.
        
        The sword rested in the earth for thirteen centuries, returning to the darkness 
        from which its metal was first drawn. When archaeologists uncovered it, they 
        found corrosion and soil, but beneath—still there—the pattern welding, the 
        careful craftsmanship, the respect for the warrior it accompanied. Every sword 
        tells two stories: the life of the one who wielded it, and the skill of the 
        one who forged it. Both stories are here, waiting in the steel.
    """,
    
    "story7": """
        The Ashmolean Museum began with John Tradescant's "Ark"—a cabinet of curiosities 
        assembled in the 1600s, perhaps the first museum collection in England. Tradescant 
        traveled the world bringing back wonders: a dodo, a volcanic rock from Vesuvius, 
        a flying squirrel, Guy Fawkes' lantern, Powhatan's mantle, coins, shells, and 
        countless "rarities" that amazed visitors.
        
        In Tradescant's garden in Lambeth, you could see the first pineapple grown in 
        England, plants from Virginia, flowers from the Mediterranean. His collection 
        was called "The Ark" because, like Noah's vessel, it preserved specimens of 
        Earth's diversity. It was science and spectacle combined, an attempt to gather 
        the whole world under one roof.
        
        When Elias Ashmole inherited and donated the collection to Oxford in 1683, the 
        Ashmolean Museum was born—the world's first university museum. Tradescant's 
        curiosity became institution, his personal ark became public treasure. Today, 
        millions walk through galleries that exist because one man couldn't stop asking 
        "What else is out there?" The Ark has landed, but the voyage of discovery 
        continues—every object a port of call, every display case a window to another 
        world.
    """,
    
    "story8": """
        The Parian Marble, also called the Marmor Parium, is a chronological table carved 
        in Greek on a marble slab around 264 BCE. It lists dates and events from Greek 
        mythology and history, beginning with the reign of Cecrops, the first king of 
        Athens (1581 BCE by its reckoning), down to 264 BCE when it was carved.
        
        This isn't just history—it's how ancient Greeks understood their own past. The 
        marble treats myths and historical events with equal seriousness: the flood of 
        Deucalion, the founding of the Eleusinian Mysteries, the first Olympiad, the 
        birth of Homer. To the Greeks, these weren't separate categories. The past was 
        continuous, divine and human events intertwined.
        
        Discovered on the island of Paros in the 1600s, this fragment came to Oxford 
        where generations of scholars have puzzled over its dates and entries. It's a 
        ghost of an ancient library, a bookmark in a civilization's memory. When you 
        read these carved lines, you're seeing the past through Greek eyes, standing 
        in their timeline, measuring history by their markers. The marble endures, 
        still counting, still remembering, a clock that stopped ticking but never 
        stopped telling time.
    """,
    
    "story9": """
        In the Pitt Rivers Museum, dim lighting reveals rows of ceremonial axes—jade, 
        stone, greenstone—from cultures across the Pacific. These weren't tools for 
        chopping wood. These were power made tangible, authority carved into stone, 
        connections between earth and ancestors given physical form.
        
        The Maori mere, the jade clubs of chiefs, were taonga—treasures with their own 
        mana, their own spiritual essence. They were named, their lineages remembered, 
        passed down through generations. To hold such an axe was to hold the strength 
        of those who held it before, to touch a chain of hands stretching back to the 
        time when the stone was first shaped.
        
        Lieutenant-General Pitt Rivers collected these objects believing they showed 
        the "evolution" of human culture. He was wrong about that—these aren't primitive 
        versions of European tools but sophisticated expressions of different worldviews. 
        Yet his collection preserves something valuable: the diversity of human imagination, 
        the thousand different ways people have carved meaning into stone. Each axe is a 
        philosophy made solid. Each blade reflects a different answer to the question: 
        What is sacred? What is worth making beautiful? What should last?
    """,
    
    "story10": """
        In the Museum of the History of Science hangs a blackboard—just a blackboard, 
        marked with chalk equations, seemingly ordinary. Except these equations were 
        written by Albert Einstein during a lecture at Oxford on May 16, 1931, exploring 
        his evolving theories about the expanding universe.
        
        The board was never erased. Someone recognized that history was written there 
        in chalk dust, that those symbols represented a mind grappling with the nature 
        of reality itself. Einstein was still refining his ideas about cosmology, still 
        arguing with the evidence that the universe was expanding—something he'd initially 
        resisted with his cosmological constant.
        
        The chalk is fading now, the equations growing faint. But they remain visible: 
        mathematics as thought made visible, genius captured mid-lecture, the moment when 
        Einstein shared his vision of curved spacetime with a room of Oxford scholars. 
        The blackboard is a window into the process of discovery—not polished theory from 
        textbooks, but working ideas, hypotheses in progress, the actual chalk-marks of 
        someone trying to understand the universe. Stand before it and you're attending 
        that 1931 lecture, watching Einstein think, seeing the moment when human consciousness 
        reached for the stars and wrote equations to explain their dance.
    """,
    
    "story11": """
        In the Ashmolean's Aegean collection stands a small faience figurine—the Minoan 
        Snake Goddess, or perhaps a priestess. She rises barely eight inches tall, yet 
        she commands attention. Her arms are raised, serpents coiling around them, her 
        bodice open in the Minoan style, her eyes fixed on eternity. She was made on 
        Crete around 1600 BCE, when Minoan civilization was at its height.
        
        The snakes she holds weren't symbols of evil but of rebirth, transformation, 
        the earth's power. In Minoan culture, women held positions of religious authority, 
        and the snake goddess represents a world where divine power wore a female face. 
        Her bare breasts aren't scandalous but sacred—this is fertility, life-force, 
        the creative power of the universe made manifest.
        
        She was found in the palace at Knossos, in a repository of sacred objects. For 
        three and a half thousand years, she waited in darkness. When British archaeologist 
        Arthur Evans uncovered her, he found a civilization that challenged Victorian 
        assumptions about the past. Here was a Bronze Age culture where women weren't 
        subordinate, where the goddess was supreme. The snake priestess stands in her 
        case now, arms forever raised, serpents forever coiled, carrying secrets of a 
        world where divinity and femininity were one.
    """,
    
    "story12": """
        Beneath your feet at the Ashmolean might have been a Roman mosaic much like 
        the one displayed on the wall—geometric patterns, mythological scenes, all 
        assembled from thousands of tiny tesserae, each carefully placed. This particular 
        mosaic dates from the fourth century CE, excavated from a Romano-British villa 
        in Oxfordshire.
        
        Imagine the craftsman on his knees, setting each small stone cube, creating from 
        fragments a picture that would last millennia. The mosaic depicts Bacchus, god 
        of wine, surrounded by creatures and vines. It graced the floor of a wealthy 
        Roman-Briton's dining room, where guests reclined on couches, eating and drinking 
        while literally standing on divine imagery.
        
        The villa collapsed, the empire fell, and the mosaic was buried under centuries 
        of English soil. Plows passed over it, crops grew above it, history moved on. 
        Yet the tesserae remained in place, patient, waiting. When archaeologists 
        revealed it again, the colors were still bright—reds, yellows, blacks, blues. 
        A message from Roman Britain: we were here, we lived well, we made beauty that 
        would outlast us. The mosaic has fulfilled that promise, surviving longer than 
        the empire that created it.
    """,
    
    "story13": """
        The Ure Greek Vase in the Ashmolean is a red-figure krater, painted in Athens 
        around 460 BCE. It shows athletes at the gymnasium—young men, perfectly rendered, 
        their muscles defined with confident brushstrokes, engaged in the activities that 
        consumed the Greek ideal: training, competing, striving for excellence.
        
        The vase-painter knew anatomy like a sculptor. Each figure moves with grace, 
        frozen mid-action yet somehow still alive. One youth scrapes oil from his skin 
        with a strigil. Another holds a discus. A trainer watches critically. This wasn't 
        just decoration—this was propaganda for a way of life, where the perfection of 
        the body reflected the perfection of the soul.
        
        The vase would have been used at symposia, those legendary Greek drinking parties 
        where men reclined and discussed philosophy, poetry, and politics. As wine was 
        poured from this krater, the athletes on its surface reminded viewers of Greek 
        values: discipline, competition, beauty, and the pursuit of arete—excellence in 
        all things. Twenty-five centuries later, the vase still preaches that sermon, 
        the athletes still frozen in their perfect youth, the Greek dream still visible 
        in glaze and clay.
    """,
    
    "story14": """
        The ichthyosaur fossil in Oxford's Natural History Museum stretches across its 
        display, a marine reptile from the age of dinosaurs, when oceans teemed with 
        creatures stranger than myth. This particular specimen was found along the 
        Jurassic Coast, possibly by Mary Anning, the legendary fossil hunter whose 
        discoveries revolutionized paleontology in the 1800s.
        
        Look at the creature's shape—streamlined like a dolphin, because evolution 
        solves the same problems with the same solutions. The ichthyosaur's ancestors 
        were land reptiles that returned to the sea, their legs becoming flippers, their 
        bodies adapting to an aquatic life. For 150 million years, ichthyosaurs ruled 
        the Mesozoic seas, then vanished in a mass extinction.
        
        When Mary Anning found these "fish lizards," science was still debating whether 
        extinction was even possible. Religious authorities argued that God would never 
        let His creations die out. But here was proof—an entire order of animals, 
        magnificently adapted, hugely successful, yet gone forever. The ichthyosaur 
        teaches a hard lesson: adaptation is no guarantee of survival. Success is 
        temporary. Everything that lives will one day be a fossil, or not even that—
        just a gap in the record, a question mark in stone.
    """,
    
    "story15": """
        The Giant Irish Deer rises in the Natural History Museum, its antlers spreading 
        twelve feet across—the largest of any known deer species. Despite the name, it 
        lived across Europe and Asia during the last ice age, vanishing about 7,700 years 
        ago. Those antlers, magnificent and deadly, may have contributed to its extinction.
        
        Each year, the stag grew those massive antlers, using enormous amounts of calcium 
        and energy. They were weapons, yes, but also advertisements—signs of fitness, 
        health, genetic superiority. The bigger the antlers, the more attractive to females, 
        the more successful in breeding. Sexual selection drove the antlers larger and larger, 
        generation by generation, until they became almost absurdly huge.
        
        Then the ice age ended. Forests grew denser. Those antlers that had been such an 
        advantage became a liability—catching on branches, requiring too much energy in a 
        changing climate. Evolution's triumph became evolution's trap. The Giant Irish Deer 
        stands as a warning: sometimes the very thing that makes you successful can become 
        the thing that dooms you. Adapt or die. And sometimes, you've adapted yourself into 
        a corner. The antlers remain, spread wide in permanent display—beautiful, impressive, 
        and extinct.
    """,
    
    "story16": """
        In the Bodleian Library's collection rests a medieval illuminated manuscript, its 
        pages glowing with gold leaf and vibrant pigments ground from lapis lazuli, 
        cinnabar, and verdigris. Each page is a garden of letters, where text blossoms 
        into elaborate borders, where capital letters become architectural wonders 
        inhabited by tiny creatures.
        
        This Book of Hours dates from the fifteenth century, made for a wealthy patron 
        who commissioned months or years of a scribe's life, an illuminator's artistry, 
        a binder's craft. It was a prayer book, meant to guide its owner through the 
        daily devotions—prayers for specific hours of the day, psalms for every occasion, 
        calendars marking saints' feast days.
        
        Look closely at the margins. There you'll find the sacred mixed with the profane—
        angels alongside grotesques, biblical scenes beside hunting rabbits and feuding 
        snails. Medieval scribes had a sense of humor. They spent their lives copying 
        holy words, but in the margins, they let their imaginations run wild. The 
        manuscript is more than a prayer book. It's a window into medieval minds, where 
        devotion and whimsy lived side by side, where every page was both worship and art, 
        where the word of God deserved to be beautiful.
    """,
    
    "story17": """
        The Lewis Chessmen sit in the Ashmolean—not the famous majority in the British 
        Museum, but a few precious pieces from the same twelfth-century cache. Carved 
        from walrus ivory, these chess pieces were found buried on the Isle of Lewis in 
        Scotland in 1831. They may have been a merchant's stock, hidden and never retrieved, 
        waiting eight centuries to be discovered.
        
        The craftsmanship is extraordinary. Kings sit on thrones, looking worried. Queens 
        rest their chins on their hands, contemplating strategy. Berserkers bite their 
        shields in battle fury. These aren't abstract game pieces—they're characters, each 
        with personality, each telling a story. They were probably carved in Trondheim, 
        Norway, during the age of Norse influence in the northern isles.
        
        What's haunting is the emotion in those tiny faces. The carver understood human 
        expression—anxiety, determination, rage. Eight hundred years ago, someone sculpted 
        these pieces with such skill that we still see the personalities. They were meant 
        for a game, yes, but they became art. And they pose a mystery: why were they buried? 
        Who was meant to retrieve them? What interrupted that plan? The chessmen don't answer. 
        They just sit on their board, frozen mid-game, waiting for a player who never came.
    """,
    
    "story18": """
        In the Pitt Rivers Museum, in dim cases that visitors sometimes miss, are tsantsas—
        shrunken heads from the Shuar people of Ecuador and Peru. These aren't curiosities 
        or grotesqueries. They're sacred objects, treated with deep respect by those who 
        made them, representing a complex worldview about life, death, and the soul.
        
        The Shuar believed that shrinking an enemy's head trapped the victim's avenging 
        spirit, preventing it from taking revenge. The process was elaborate, ritualized, 
        taking days of careful work. The tsantsa was then kept as protection for the 
        community. This wasn't cruelty—it was spiritual technology, a way of dealing with 
        the dangerous forces unleashed by killing.
        
        The museum labels warn that many "shrunken heads" in collections are fakes, made 
        for the tourist trade after Europeans developed a ghoulish fascination with them. 
        But the authentic tsantsas here represent genuine cultural practices, now largely 
        abandoned. They ask difficult questions: What makes a cultural practice sacred 
        versus savage? Who decides? The heads preserve not just physical remains but the 
        memory of a worldview—where the boundary between the living and the dead was 
        porous, where enemies remained dangerous even after death, where elaborate rituals 
        kept communities safe from spiritual harm.
    """,
    
    "story19": """
        The samurai armor in the Ashmolean stands on display, layer upon layer of lacquered 
        metal and silk cord, a complete suit of armor from Edo-period Japan. The kabuto 
        helmet rises to a point, the mempo face-mask bears a frozen expression of fierce 
        determination, and the do chest-plate is decorated with the owner's mon—family crest.
        
        Each piece of armor was crafted not just for protection but for meaning. The colors 
        indicated rank, the decorations told of lineage and achievement. Wearing such armor 
        wasn't simply practical—it was a statement of identity, honor, and commitment to 
        bushido, the way of the warrior. The samurai lived by a code: loyalty, courage, 
        self-discipline, and an acceptance of death that bordered on romance.
        
        This armor survived the samurai class itself. When the Meiji Restoration modernized 
        Japan in the 1860s, the samurai were abolished, their swords declared illegal, their 
        way of life made obsolete by rifles and conscript armies. Yet the armor remains, 
        preserved by collectors who recognized that it represented more than military 
        equipment. It was art, philosophy, and history made wearable. The empty suit stands 
        at attention, waiting for a warrior who will never return, a symbol of a code that 
        proved both beautiful and ultimately unsustainable in the face of modernity.
    """,
    
    "story20": """
        The astrolabe in the Museum of the History of Science is a medieval Islamic 
        instrument, brass engraved with Arabic inscriptions, made in Persia around 1300 CE. 
        It's both a scientific instrument and a work of art—functional precision married 
        to decorative beauty in a way that exemplifies Islamic scientific tradition.
        
        An astrolabe could determine the time, locate the positions of stars and planets, 
        calculate the direction to Mecca for prayer, measure heights and distances, and 
        even serve as an analog computer for astronomical calculations. It compressed the 
        celestial sphere onto a flat plane through stereographic projection—a mathematical 
        elegance that let travelers carry the heavens in their hands.
        
        Islamic scholars preserved and expanded Greek astronomical knowledge during Europe's 
        Middle Ages, adding their own innovations and observations. This astrolabe represents 
        that golden age of Islamic science—when Baghdad and Cordoba were centers of learning, 
        when observatories dotted the Islamic world, when scholars of all religions collaborated 
        on understanding the cosmos. The instrument still works. Its pointers still align with 
        stars, its scales still calculate accurately. Eight centuries of dust haven't dimmed 
        its precision. It's a reminder that scientific truth transcends culture, and that beauty 
        and function need not be separate.
    """,
    
    "story21": """
        Charles Dodgson—better known as Lewis Carroll—was an Oxford mathematics don, but he 
        was also a pioneer photographer. The Museum of the History of Science holds one of his 
        cameras, along with examples of his work. In the 1850s-1870s, photography was cutting-edge 
        technology, and Carroll mastered it with the same precision he brought to logic and 
        mathematics.
        
        His subjects were often children, particularly Alice Liddell, the real girl who inspired 
        Alice's Adventures in Wonderland. Carroll's photographs show technical skill but also 
        artistic vision—careful composition, attention to light, an ability to capture personality. 
        He would pose his subjects as characters from stories, creating narrative photographs 
        decades before cinema made moving pictures possible.
        
        The camera itself is a wooden box, plates and chemicals required, long exposure times 
        demanding stillness from subjects. Photography then was a chemical adventure, a physical 
        challenge, an art requiring patience. Carroll would disappear under a dark cloth, emerging 
        with glass plates that had captured moments in silver salts. The camera captures something 
        else too—the intersection of science and art, mathematics and imagination, that defined 
        Carroll himself. The man who created Wonderland was also the man measuring light, mixing 
        chemicals, calculating exposures. The camera proves that logic and fantasy can exist in 
        the same hands.
    """,
    
    "story22": """
        "The Light of the World" by William Holman Hunt hangs in Keble College Chapel, one 
        of the most reproduced religious paintings in history. Christ stands at a weed-covered 
        door, holding a lantern, knocking. The door has no handle on the outside—it can only 
        be opened from within. The symbolism is clear: Christ knocks, but the soul must choose 
        to let him in.
        
        Hunt was a Pre-Raphaelite, committed to painting with intense realism and symbolic 
        depth. He worked on the painting at night, by actual lantern-light, to get the 
        illumination exactly right. Every detail carries meaning—the crown of thorns suggests 
        suffering, the priestly robes suggest authority, the overgrown door suggests a soul 
        long neglected. Yet Christ waits patiently, lantern in hand, ready to illuminate 
        the darkness.
        
        Hunt painted two more versions of this image later in life, and countless prints were 
        made. The painting toured the British Empire, was sent to battlefields as inspiration, 
        hung in churches worldwide. Whatever one's religious beliefs, the image has power: a 
        figure of patience and light, standing in darkness, waiting for a door to open. The 
        lantern glows, the light falls on the door, the knock echoes across centuries. The 
        painting asks a question: What doors in ourselves remain closed? What light are we 
        keeping out?
    """,
    
    "story23": """
        The Ashmolean holds several drawings by Michelangelo—quick sketches in red chalk, 
        studies for sculptures that would become masterpieces. These aren't finished artworks. 
        They're thinking made visible, the master at work, trying angles, testing proportions, 
        working out how marble could become flesh.
        
        One drawing shows studies of a male torso—muscles understood with anatomical precision, 
        line after line exploring the structure beneath the skin. Michelangelo famously dissected 
        corpses to understand human anatomy, knowledge forbidden yet essential for achieving the 
        realism his sculptures demanded. The Renaissance believed in studying nature directly, 
        even when nature meant dead bodies and church prohibition.
        
        What's remarkable is the confidence in these lines. Michelangelo drew quickly, surely, 
        his hand moving with the certainty of absolute mastery. Yet even here, you can see him 
        thinking—a line tried and abandoned, an angle reconsidered, the work of refinement. 
        These are sketches, but they're Michelangelo sketches, which means they're better than 
        most artists' finished works. The drawing is a window into genius at work—not the 
        polished marble of the Sistine Chapel, but the moment before creation, when the hand 
        is still searching for the perfect line, and the perfect line is just about to be found.
    """,
    
    "story24": """
        The Islamic ceramic bowl in the Ashmolean glows with turquoise and cobalt blue, covered 
        in geometric patterns and Arabic calligraphy that flows like water. Made in Persia around 
        the 13th century, it exemplifies Islamic art's genius—transforming functional objects into 
        vehicles for spiritual contemplation through pattern, color, and sacred text.
        
        Islamic art often avoids depicting living creatures, instead exploring the infinite through 
        geometry. These patterns—interlocking stars, tessellating shapes, arabesques that could 
        continue forever—represent the mathematical perfection underlying creation. The patterns 
        suggest infinity, the underlying order of the universe, the divine geometry that structures 
        reality itself.
        
        The calligraphy wrapping the bowl's rim might be poetry, Quranic verses, or blessings for 
        the owner. In Islamic culture, beautiful writing is itself a form of worship—God's words 
        deserve to be rendered beautifully. The bowl was functional, yes, meant to hold food or 
        water. But it was also meant to elevate daily life, to make every meal an aesthetic 
        experience, to surround the mundane with the beautiful. The bowl proclaims that there need 
        be no separation between art and life, between beauty and utility, between the practical 
        and the divine. Everything can be made beautiful. Everything deserves to be.
    """,
    
    "story25": """
        The Bodleian Library holds a Shakespeare First Folio, published in 1623, seven years after 
        the playwright's death. Without this book, half of Shakespeare's plays would have been lost. 
        "Macbeth," "The Tempest," "As You Like It," "Julius Caesar"—all unpublished at Shakespeare's 
        death, preserved only because his fellow actors, John Heminges and Henry Condell, collected 
        and printed them.
        
        The Folio was expensive—a luxury item, not everyone's paperback. It cost about one pound, 
        when a skilled worker earned thirty pounds a year. But Heminges and Condell believed 
        Shakespeare's "trifles" deserved preservation. They wrote in the preface that they published 
        these plays "onely to keepe the memory of so worthy a Friend & Fellow alive as was our 
        Shakespeare."
        
        Open the Folio and you're reading the same words that readers have encountered for four 
        centuries. The same "To be or not to be," the same "We are such stuff as dreams are made on," 
        the same "If music be the food of love, play on." The paper is thick, the type uneven, the 
        spelling archaic. But the words—the words pulse with life. Shakespeare never saw this book. 
        He had no idea his plays would be read four hundred years later, studied in every language, 
        performed on every continent. The Folio made him immortal. "He was not of an age," Heminges 
        and Condell wrote, "but for all time." The book in its case proves them right.
    """
}

def get_user_id():
    """Get or create user ID from session"""
    if 'user_id' not in session:
        session['user_id'] = f"demo_user_{datetime.now().timestamp()}"
    return session['user_id']

@app.route('/')
def index():
    """Home page - mood check and story recommendations"""
    user_id = get_user_id()
    
    # Get user profile if exists
    user = recommender.users.get(user_id)
    current_mood = user.current_mood.value if user and user.current_mood else None
    recommendation_mix = user.recommendation_mix if user else 0.5
    
    # Get user stats
    stats = {
        'stories_read': len(user.viewed_stories) if user else 0,
        'stories_completed': len(user.completed_stories) if user else 0,
        'favorites': len(user.favorited_stories) if user else 0,
        'mood_trend': user._mood_trend if user else None,
        'last_completed': None
    }
    
    if user and user.last_completed_story and user.last_completed_story in recommender.stories:
        stats['last_completed'] = recommender.stories[user.last_completed_story].title
    
    return render_template('index.html', 
                         current_mood=current_mood,
                         recommendation_mix=recommendation_mix,
                         stats=stats,
                         user_id=user_id)

@app.route('/set_mood', methods=['POST'])
def set_mood():
    """Set user's current mood"""
    user_id = get_user_id()
    mood_value = float(request.form['mood'])
    
    event = AnalyticsEvent(
        user_id,
        'mood_general',
        datetime.now(),
        mood_score=mood_value
    )
    recommender.add_event(event)
    
    return redirect(url_for('index'))

@app.route('/set_slider', methods=['POST'])
def set_slider():
    """Set recommendation mix slider"""
    user_id = get_user_id()
    position = float(request.form['position'])
    
    event = AnalyticsEvent(
        user_id,
        'slider_position',
        datetime.now(),
        position=position
    )
    recommender.add_event(event)
    
    return redirect(url_for('index'))

@app.route('/recommendations')
def recommendations():
    """Show personalized recommendations"""
    user_id = get_user_id()
    
    # Get recommendations
    recs = recommender.get_recommendations(user_id, n_recommendations=8)
    
    # Prepare recommendation data
    rec_data = []
    for story_id, score in recs:
        story = recommender.stories[story_id]
        
        # Get reasons for recommendation
        reasons = []
        
        # Check if it's a good follow-up to last completed story
        user = recommender.users.get(user_id)
        if user and user.last_completed_story:
            last_story = recommender.stories.get(user.last_completed_story)
            if last_story:
                if story_id in last_story.best_next_stories:
                    effect = last_story.best_next_stories[story_id]
                    reasons.append(f"Great follow-up to '{last_story.title}' (mood effect: {effect:+.1f})")
                
                if story.theme in last_story.best_next_themes:
                    theme_effect = last_story.best_next_themes[story.theme]
                    reasons.append(f"Theme transition works well (effect: {theme_effect:+.1f})")
        
        # Check mood effectiveness
        if user and user.current_mood:
            mood_range = recommender._get_mood_range(user.current_mood.value)
            if mood_range in story.mood_effectiveness:
                effectiveness = story.mood_effectiveness[mood_range]
                if effectiveness > 0.5:
                    reasons.append(f"Works well for your current mood")
        
        # Check if favorited similar stories
        if user and user.favorited_stories:
            for fav_id in user.favorited_stories:
                similarity = recommender._story_similarity(story_id, fav_id)
                if similarity > 0.5 and fav_id in recommender.stories:
                    reasons.append(f"Similar to '{recommender.stories[fav_id].title}' (favorite)")
                    break
        
        rec_data.append({
            'id': story_id,
            'title': story.title,
            'theme': story.theme,
            'tags': story.tags,
            'score': score,
            'reasons': reasons,
            'avg_mood_change': story.avg_mood_change
        })
    
    return render_template('recommendations.html', recommendations=rec_data)

@app.route('/story/<story_id>')
def view_story(story_id):
    """View a story"""
    user_id = get_user_id()
    
    if story_id not in recommender.stories:
        return redirect(url_for('index'))
    
    story = recommender.stories[story_id]
    content = STORY_CONTENT.get(story_id, "Story content not available.")
    
    # Record view event
    event = AnalyticsEvent(
        user_id,
        'view',
        datetime.now(),
        story_id=story_id
    )
    recommender.add_event(event)
    
    # Check if already completed
    user = recommender.users.get(user_id)
    already_completed = user and story_id in user.completed_stories
    
    return render_template('story.html', 
                         story=story, 
                         content=content,
                         already_completed=already_completed)

@app.route('/complete_story/<story_id>', methods=['POST'])
def complete_story(story_id):
    """Mark story as completed"""
    user_id = get_user_id()
    
    event = AnalyticsEvent(
        user_id,
        'complete',
        datetime.now(),
        story_id=story_id
    )
    recommender.add_event(event)
    
    # Redirect to completion page with options
    return redirect(url_for('story_completed', story_id=story_id))

@app.route('/story_completed/<story_id>')
def story_completed(story_id):
    """Show post-reading options (mood and like)"""
    story = recommender.stories.get(story_id)
    if not story:
        return redirect(url_for('index'))
    
    user_id = get_user_id()
    user = recommender.users.get(user_id)
    mood_before = user.current_mood.value if user and user.current_mood else None
    
    # Check if already liked
    already_liked = user and story_id in user.favorited_stories
    
    return render_template('story_completed.html', 
                         story=story, 
                         mood_before=mood_before,
                         already_liked=already_liked)

@app.route('/submit_mood_after/<story_id>', methods=['POST'])
def submit_mood_after(story_id):
    """Submit mood after story"""
    user_id = get_user_id()
    mood_value = float(request.form['mood'])
    
    event = AnalyticsEvent(
        user_id,
        'mood_after',
        datetime.now(),
        story_id=story_id,
        mood_score=mood_value
    )
    recommender.add_event(event)
    
    # Check where to redirect
    next_page = request.form.get('next', 'recommendations')
    if next_page == 'story_completed':
        return redirect(url_for('story_completed', story_id=story_id))
    return redirect(url_for('recommendations'))

@app.route('/like_story/<story_id>', methods=['POST'])
def like_story(story_id):
    """Like a story (same as favorite)"""
    user_id = get_user_id()
    
    event = AnalyticsEvent(
        user_id,
        'favorite',
        datetime.now(),
        story_id=story_id
    )
    recommender.add_event(event)
    
    # Redirect back to where the user came from
    return redirect(request.referrer or url_for('recommendations'))

@app.route('/favorite/<story_id>', methods=['POST'])
def favorite_story(story_id):
    """Add story to favorites (legacy route, redirects to like_story)"""
    return like_story(story_id)

@app.route('/insights')
def insights():
    """Show insights about sequences and patterns"""
    user_id = get_user_id()
    
    # Get sequence insights
    insights_data = recommender.get_sequence_insights(user_id)
    
    # Get user-specific data
    user = recommender.users.get(user_id)
    user_data = None
    
    if user:
        # Get theme preferences
        theme_scores = user._get_decayed_theme_scores(datetime.now())
        
        user_data = {
            'mood_history': [(ts.strftime('%Y-%m-%d %H:%M'), mood.value) 
                           for ts, mood in user.mood_history[-10:]],
            'theme_scores': sorted(theme_scores.items(), key=lambda x: x[1], reverse=True),
            'sequences': insights_data.get('user_sequences', [])[-10:]
        }
    
    return render_template('insights.html', 
                         insights=insights_data,
                         user_data=user_data)

@app.route('/reset')
def reset():
    """Reset the demo (clear session)"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
