.PHONY: package clean

package:
	pip install --user pyinstaller tabulate
	pyinstaller --onefile src/pomodoro.py --name pomodoro

clean:
	rm -rf build dist pomodoro.spec