import sys
import tty
import termios


def selectFromList(prompt: str, options: list, format_option=None) -> int:
    """
    Interactive arrow key selection from a list.
    
    Args:
        prompt: Header text to display
        options: List of items to choose from
        format_option: Optional function to format each option (receives (index, item))
    
    Returns:
        Index of selected item, or -1 if user chose unknown ('u')
    """
    def getch():
        """Get single character from stdin"""
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    
    ptr = 0
    while True:
        # Clear and display
        print("\033[2J\033[H")  # Clear screen
        print(f"{prompt}\n")
        
        for i, option in enumerate(options):
            marker = "→" if i == ptr else " "
            if format_option:
                text = format_option(i, option)
            else:
                text = str(option)
            print(f"  {marker} {text}")
        
        print("\n↑↓ to navigate | Enter to select | 'u' for unknown")
        
        # Get input
        ch = getch()
        
        if ch == '\x1b':  # ESC sequence (arrow keys)
            getch()  # [
            direction = getch()
            if direction == 'A':  # Up
                ptr = max(0, ptr - 1)
            elif direction == 'B':  # Down
                ptr = min(len(options) - 1, ptr + 1)
        elif ch in ('\r', '\n'):  # Enter
            return ptr
        elif ch in ('u', 'U'):  # Unknown
            return -1
