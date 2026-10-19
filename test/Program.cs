using System;

class Program
{
    static void Main()
    {
        Animal animal1 = new Animal();

        Animal animal2 = new Animal(
            "лев",
            5,
            4,
            AnimalType.predator,
            Habitat.land,
            Continent.Africa,
            true);

        Animal animal3 = new Animal(
            "утка",
            2,
            2,
            AnimalType.omnivore,
            Habitat.landAndWater,
            Continent.Eurasia,
            true);

        Animal animal4 = new Animal(
            "кошка",
            3,
            4,
            AnimalType.predator,
            Habitat.land,
            Continent.Eurasia,
            true);

        Console.WriteLine("- 1 животное:");
        animal1.ShowInfo();

        Console.WriteLine();

        Console.WriteLine("- 2 животное:");
        animal2.ShowInfo();

        Console.WriteLine();

        Console.WriteLine("- 3 животное:");
        animal3.ShowInfo();

        Console.WriteLine();

        Console.WriteLine("- 4 животное:");
        animal4.ShowInfo();



        Console.WriteLine();
        Console.WriteLine("- Проверка свойств:");

        animal2.Age = 6;

        Console.WriteLine("Возраст льва изменен с помощью свойства Age.");

        Console.WriteLine(
            "Имя животного через свойство Name: " + animal2.Name);



        Console.WriteLine();
        Console.WriteLine("- Сравнение животных:");

        Animal animal5 = new Animal(
            "лев",
            6,
            4,
            AnimalType.predator,
            Habitat.land,
            Continent.Africa,
            true);

        Console.WriteLine($"animal2 == animal5: {animal2 == animal5}");
        Console.WriteLine($"animal2 != animal5: {animal2 != animal5}");



        Console.WriteLine();
        Console.WriteLine("- Класс Figure:");

        Figure square = new Figure(5);

        Figure rectangle = new Figure(6, 4);

        Figure triangle = new Figure(3, 4, 5);

        Figure impossibleTriangle = new Figure(1, 2, 10);

        Console.WriteLine(
        $"Площадь треугольника 1, 2, 10: {impossibleTriangle.Square:F2}");

        Console.WriteLine($"Площадь квадрата: {square.Square}");
        Console.WriteLine($"Площадь прямоугольника: {rectangle.Square}");
        Console.WriteLine($"Площадь треугольника: {triangle.Square:F2}");

        Console.WriteLine();
        Console.WriteLine("- Для завершения нажмите Enter...");
        Console.ReadLine();
    }
}
