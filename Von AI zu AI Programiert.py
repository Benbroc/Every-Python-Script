python
import random

def number_guessing_game():
    # Generate a random number between 1 and 100
    number_to_guess = random.randint(1, 100)
    
    # Initialize the number of attempts
    attempts = 0
    
    print("Welcome to the number guessing game!")
    print("I'm thinking of a number between 1 and 100.")
    
    while attempts < 6:
        # Ask the player for their guess
        user_guess = input("Take a guess: ")
        
        # Check if the input is a valid integer
        if not user_guess.isdigit():
            print("Invalid input. Please enter a whole number.")
            continue
        
        # Convert the input to an integer
        user_guess = int(user_guess)
        
        # Increment the number of attempts
        attempts += 1
        
        # Check if the guess is correct
        if user_guess == number_to_guess:
            print(f"Congratulations! You guessed the number in {attempts} attempts.")
            return
        
        # Provide a hint if the guess is incorrect
        elif user_guess < number_to_guess:
            print("Too low! Try a higher number.")
        else:
            print("Too high! Try a lower number.")
    
    # If the player runs out of attempts, reveal the number
    print(f"Sorry, you didn't guess the number. The number was {number_to_guess}.")

# Run the game
if __name__ == "__main__":
    number_guessing_game()