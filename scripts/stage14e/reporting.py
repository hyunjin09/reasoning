"""Small formatting helpers for CPU-only closure reports."""


def markdown_blocks(blocks):
    """Keep consecutive table rows together while separating prose blocks."""
    result = ''
    for block in blocks:
        separator = '\n' if result and result.rstrip().splitlines()[-1].startswith('|') and block.startswith('|') else '\n\n'
        result += (separator if result else '') + block
    return result + '\n'
