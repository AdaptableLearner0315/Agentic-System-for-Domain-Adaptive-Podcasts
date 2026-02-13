"""
Image Generation Prompts Configuration
Author: Sarath

Contains all image generation prompts for the visual enhancement pipeline.

SAFETY CONSTRAINT: No artist faces or direct depictions of real people.
All prompts should use settings, objects, landscapes, and atmospheric imagery.
"""

# Base style suffix for all prompts
CINEMATIC_STYLE = ", cinematic photography, documentary style, photorealistic, film grain, 35mm film aesthetic, professional lighting, high quality"

# Hook section image prompts (2 images, ~20-40s each)
HOOK_PROMPTS = [
    {
        "id": "hook_img_1",
        "prompt": "10-year-old Icelandic girl performing on school stage, piano visible, spotlight illuminating her face as she sings with intense otherworldly expression, wooden auditorium filled with captivated audience, Reykjavik 1975, historic moment captured",
        "sentences": "1-4",
        "duration_hint": "~30s"
    },
    {
        "id": "hook_img_2",
        "prompt": "Epic wide shot of volcanic Iceland landscape with dramatic sky, small figure of young artist silhouetted against the vastness, symbolizing the beginning of an extraordinary journey from isolation to global icon",
        "sentences": "5-6",
        "duration_hint": "~16s"
    }
]

# Module-specific image prompts
# SAFETY: Avoid direct face depictions of real artists. Use settings, objects, atmospheres.
MODULE_PROMPTS = {
    1: [
        {
            "id": "module_1_img_1",
            "prompt": "Misty volcanic landscape Iceland, geothermal steam rising from ground, dramatic moody overcast sky, wide cinematic shot"
        },
        {
            "id": "module_1_img_2",
            "prompt": "Bohemian commune buildings 1960s Iceland, small artistic community houses, warm nostalgic color tones, hippie era"
        },
        {
            "id": "module_1_img_3",
            "prompt": "Communal creative space filled with musical instruments, artists working together, warm golden hour lighting through windows"
        },
        {
            "id": "module_1_img_4",
            "prompt": "Small child hands on piano keys, serious young girl practicing classical music, intimate documentary close-up shot"
        },
        {
            "id": "module_1_img_5",
            "prompt": "Vinyl records spinning on vintage turntable, Jimi Hendrix album cover visible, 1970s stereo equipment, warm lighting"
        },
        {
            "id": "module_1_img_6",
            "prompt": "Aurora borealis northern lights dancing over Reykjavik, geothermal pools steaming in foreground, magical night sky"
        },
        {
            "id": "module_1_img_7",
            "prompt": "Young serious-faced Icelandic girl gazing at dramatic volcanic landscape, contemplative mood, wind in hair"
        },
    ],
    2: [
        {
            "id": "module_2_img_1",
            "prompt": "School auditorium Iceland 1975, wooden stage with piano, vintage recording equipment set up, anticipation atmosphere"
        },
        {
            "id": "module_2_img_2",
            "prompt": "11-year-old girl at professional studio microphone, recording studio 1977, concentrated expression, historic moment"
        },
        {
            "id": "module_2_img_3",
            "prompt": "Debut album cover design session in progress, record label office 1977, creative process, vintage aesthetic"
        },
        {
            "id": "module_2_img_4",
            "prompt": "Teenage girl in 1980s Iceland, new wave fashion aesthetic, local celebrity vibe, restless creative energy"
        },
        {
            "id": "module_2_img_5",
            "prompt": "1980s Iceland Reykjavik street scene, emerging punk and new wave culture, youth gathering, rebellion brewing"
        },
    ],
    3: [
        {
            "id": "module_3_img_1",
            "prompt": "Icelandic punk rock scene 1980s, small smoky underground club interior, raw DIY energy, dim lighting"
        },
        {
            "id": "module_3_img_2",
            "prompt": "Grainy documentary footage aesthetic, wild energetic performance on tiny stage, feral intensity, punk rock"
        },
        {
            "id": "module_3_img_3",
            "prompt": "Young female punk singer commanding small stage, wild spiky hair and dramatic makeup, defying boundaries"
        },
        {
            "id": "module_3_img_4",
            "prompt": "Political gathering with experimental avant-garde music performance, anarcho-punk collective, KUKL era Iceland"
        },
        {
            "id": "module_3_img_5",
            "prompt": "Artistic wedding photo 1986 Iceland, young musician couple, bohemian community celebration, hopeful"
        },
        {
            "id": "module_3_img_6",
            "prompt": "The Sugarcubes band formation group photo, Icelandic musicians, breaking international barriers, hopeful new chapter"
        },
    ],
    4: [
        {
            "id": "module_4_img_1",
            "prompt": "Top of the Pops TV studio performance 1988, international spotlight, colorful 80s TV set, global breakthrough moment"
        },
        {
            "id": "module_4_img_2",
            "prompt": "Music album charts showing international success, press coverage collage, million copies celebration, 1980s media"
        },
        {
            "id": "module_4_img_3",
            "prompt": "Band tension in recording studio, creative differences visible through body language, isolated artist, melancholic mood"
        },
        {
            "id": "module_4_img_4",
            "prompt": "Solo female artist in modern 1990s recording studio, mixing boards and electronic equipment, orchestral meets electronic"
        },
        {
            "id": "module_4_img_5",
            "prompt": "Evolution montage showing iconic artistic looks through decades, avant-garde fashion, bold reinvention"
        },
        {
            "id": "module_4_img_6",
            "prompt": "Iceland volcanic landscape with ethereal artistic overlay, full circle journey, revolutionary artist legacy, epic conclusion"
        },
    ]
}
