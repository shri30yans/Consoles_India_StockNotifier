"""Heroku-style entry (Procfile); same as main."""

from stock_notifier.runner import main

if __name__ == "__main__":
    main()
