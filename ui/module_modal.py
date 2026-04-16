import os
import re

# Video URL for March Accreditation (env: MARCH_ACCREDITATION_VIDEO_URL).
# For in-modal playback, Slack's video block needs an embed URL and thumbnail.
# We derive these from YouTube watch URLs; otherwise set MARCH_ACCREDITATION_VIDEO_EMBED_URL and
# MARCH_ACCREDITATION_VIDEO_THUMBNAIL_URL. App must have links.embed:write and the video domain in unfurl domains.
DEFAULT_MARCH_ACCREDITATION_VIDEO_URL = "https://www.example.com/march-accreditation-video"


def _march_accreditation_video_urls():
    """Return (watch_url, embed_url, thumbnail_url). embed/thumbnail may be None (then we show link only)."""
    watch = os.environ.get("MARCH_ACCREDITATION_VIDEO_URL", DEFAULT_MARCH_ACCREDITATION_VIDEO_URL)
    embed = os.environ.get("MARCH_ACCREDITATION_VIDEO_EMBED_URL")
    thumb = os.environ.get("MARCH_ACCREDITATION_VIDEO_THUMBNAIL_URL")
    if embed and thumb:
        return (watch or embed, embed, thumb)
    # Derive from YouTube
    m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)", watch)
    if m:
        vid = m.group(1)
        return (watch, f"https://www.youtube.com/embed/{vid}?feature=oembed", f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg")
    return (watch, None, None)


def create_module_start_modal(module_name, module_description, due_date, assignment_id, module_id=None, trailhead_url=""):
    """Create modal for starting a module. March Accreditation (predefined_6) shows video + upcoming changes + Acknowledge button only."""
    if module_id == "predefined_6":
        return _create_march_accreditation_modal(assignment_id, due_date)

    # Build resource buttons
    resource_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📖 *Learning Resources*\n\n⚠️ *You must click the button below to access the learning materials before you can complete this module:*"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "🌐 Open Learning Materials"
                },
                "url": "https://google.com",
                "action_id": "open_learning_materials"
            }
        },
    ]

    # Add Trailhead button if URL is set
    if trailhead_url:
        resource_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🏔️ *Trailhead*\nComplete the corresponding trail or module on Trailhead:"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "🏔️ Open in Trailhead",
                    "emoji": True
                },
                "url": trailhead_url,
                "action_id": "open_trailhead_module"
            }
        })

    return {
        "type": "modal",
        "callback_id": "module_start_modal",
        "title": {
            "type": "plain_text",
            "text": f"📚 {module_name}"
        },
        "submit": {
            "type": "plain_text",
            "text": "Mark as Complete"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "private_metadata": str(assignment_id),
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📚 {module_name}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:* {module_description}\n*Due Date:* {due_date}"
                }
            },
            {
                "type": "divider"
            },
        ] + resource_blocks + [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "⚠️ *Step 1: Access Learning Materials*\n\nClick the button below to confirm you have accessed the learning materials:"
                },
                "block_id": "materials_accessed_status",
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ I Have Accessed Learning Materials"
                    },
                    "action_id": f"materials_accessed_{assignment_id}",
                    "style": "primary"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "After reviewing the materials, please acknowledge that you have completed the module:"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Acknowledge completion"
                },
                "accessory": {
                    "type": "checkboxes",
                    "action_id": "acknowledge_completion",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "I have reviewed the learning materials and completed this module"
                            },
                            "value": "acknowledged"
                        }
                    ]
                },
                "block_id": "acknowledge_checkbox"
            }
        ]
    }


def _create_march_accreditation_modal(assignment_id, due_date):
    """March Accreditation: one video + upcoming changes in March + Acknowledge button. Acknowledge marks as completed."""
    watch_url, embed_url, thumbnail_url = _march_accreditation_video_urls()
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "March Accreditation", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Due:* {due_date}"}},
        {"type": "divider"},
    ]
    if embed_url and thumbnail_url:
        blocks.append({
            "type": "video",
            "title": {"type": "plain_text", "text": "March Accreditation video", "emoji": True},
            "title_url": watch_url,
            "video_url": embed_url,
            "thumbnail_url": thumbnail_url,
            "alt_text": "March Accreditation video",
        })
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"Click the play button above to watch in this window, or <{watch_url}|open in browser>."},
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"📹 *Watch the video*\n\n<{watch_url}|Watch March Accreditation video>",
            },
        })
    blocks.extend([
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "📋 *Upcoming changes in March*\n\nPlease review the upcoming changes and acknowledge below when done.",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Click *Acknowledge* to confirm you have watched the video and reviewed the upcoming changes. This will mark the module as completed.",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Acknowledge", "emoji": True},
                "action_id": f"acknowledge_module_{assignment_id}",
                "style": "primary",
            },
        },
    ])
    return {
        "type": "modal",
        "callback_id": "march_accreditation_modal",
        "title": {"type": "plain_text", "text": "March Accreditation"},
        "close": {"type": "plain_text", "text": "Close"},
        "private_metadata": str(assignment_id),
        "blocks": blocks,
    }
