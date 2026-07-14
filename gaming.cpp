#include <iostream>
#include <conio.h>
#include <windows.h>
#include <ctime>

using namespace std;

const int WIDTH = 20;
const int HEIGHT = 20;

int carPos = WIDTH / 2;
int obstacleX, obstacleY;
int score = 0;
bool gameOver = false;

void gotoxy(int x, int y) {
    COORD c;
    c.X = x;
    c.Y = y;
    SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), c);
}

void draw() {
    gotoxy(0, 0);

    for (int i = 0; i <= HEIGHT; i++) {
        for (int j = 0; j <= WIDTH; j++) {

            if (j == 0 || j == WIDTH)
                cout << "|";
            else if (i == HEIGHT && j == carPos)
                cout << "A";      // Player's car
            else if (i == obstacleY && j == obstacleX)
                cout << "#";      // Obstacle
            else
                cout << " ";
        }
        cout << endl;
    }

    cout << "Score: " << score << endl;
    cout << "Use LEFT and RIGHT arrow keys to move." << endl;
}

void input() {
    if (_kbhit()) {
        char ch = _getch();

        if (ch == 75 && carPos > 1)          // Left arrow
            carPos--;
        else if (ch == 77 && carPos < WIDTH - 1) // Right arrow
            carPos++;
    }
}

void logic() {
    obstacleY++;

    if (obstacleY > HEIGHT) {
        obstacleY = 0;
        obstacleX = rand() % (WIDTH - 2) + 1;
        score++;
    }

    if (obstacleY == HEIGHT && obstacleX == carPos) {
        gameOver = true;
    }
}

int main() {
    srand((unsigned)time(0));

    obstacleX = rand() % (WIDTH - 2) + 1;
    obstacleY = 0;

    while (!gameOver) {
        draw();
        input();
        logic();
        Sleep(100);
    }

    system("cls");
    cout << "======================" << endl;
    cout << "      GAME OVER       " << endl;
    cout << "Final Score: " << score << endl;
    cout << "======================" << endl;

    return 0;
