from sorting_hat import SortingHat

if __name__ == "__main__":
    sorting_hat = SortingHat(tts_service='openai')
    # sorting_hat = SortingHat(tts_service='elevenlabs')
    sorting_hat.run()
