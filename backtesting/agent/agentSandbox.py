


import msvcrt


count = 0
print("Press 4 to count. Press Enter to finish.")

while True:
	key = msvcrt.getwch()

	if key in ("\r", "\n"):
		break

	if key == "4":
		count += 1
		print("4", end="", flush=True)

print(f"\nYou pressed 4 {count} time(s).")





