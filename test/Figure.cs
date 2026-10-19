using System;

class Figure
{
    private double _square;

    // Конструктор квадрата.
    public Figure(double side)
    {
        if (side <= 0)
            throw new ArgumentException("Сторона должна быть больше нуля.");

        _square = side * side;
    }

    // Конструктор прямоугольника.
    public Figure(double width, double height)
    {
        if (width <= 0 || height <= 0)
            throw new ArgumentException("Стороны должны быть больше нуля.");

        _square = width * height;
    }

    // Конструктор треугольника.
    public Figure(double a, double b, double c)
    {
        // Проверяем положительность сторон
        // и неравенство треугольника.
        if (a <= 0 || b <= 0 || c <= 0 ||
            a + b <= c ||
            a + c <= b ||
            b + c <= a)
        {
            _square = 0;
            return;
        }

        // Формула Герона.
        double p = (a + b + c) / 2;

        double expression =
            p * (p - a) * (p - b) * (p - c);

        // Дополнительная защита от отрицательного значения
        // под квадратным корнем.
        _square = Math.Sqrt(Math.Max(0, expression));
    }

    // Свойство только для чтения.
    public double Square
    {
        get { return _square; }
    }
}
