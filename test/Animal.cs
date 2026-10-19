using System;

enum AnimalType
{
    herbivore,
    predator,
    omnivore
}

enum Habitat
{
    land,
    water,
    air,
    landAndWater
}

enum Continent
{
    Eurasia,
    Africa,
    NorthAmerica,
    SouthAmerica,
    Australia,
    Antarctica
}

class Animal
{
    private string _name;
    private int _age;
    private int _limbsCount;
    private AnimalType _type;
    private Habitat _habitat;
    private Continent _continent;

    private bool _hasTail;

    public Animal()
    {
        _name = "неизвестное животное";
        _age = 0;
        _limbsCount = 0;
        _type = AnimalType.omnivore;
        _habitat = Habitat.land;
        _continent = Continent.Eurasia;
        _hasTail = false;
    }

    public Animal(
        string name,
        int age,
        int limbsCount,
        AnimalType type,
        Habitat habitat,
        Continent continent,
        bool hasTail)
    {
        _name = name;
        _age = age;
        _limbsCount = limbsCount;
        _type = type;
        _habitat = habitat;
        _continent = continent;
        _hasTail = hasTail;
    }

    public string Name
    {
        get
        {
            return _name;
        }
    }

    public int Age
    {
        set
        {
            _age = value;
        }
    }

    public string GetSound()
    {
        return _name switch
        {
            "лев" => "ррр",
            "собака" => "гав",
            "кошка" => "мяу",
            "утка" => "кря",
            "корова" => "муу",
            "волк" => "ауу",
            _ => "животное издает звук"
        };
    }

    public bool CanFly()
    {
        return _habitat == Habitat.air;
    }

    public bool CanSwim()
    {
        return _habitat == Habitat.water ||
               _habitat == Habitat.landAndWater;
    }

    public bool ExistsTail()
    {
        return _hasTail;
    }

    public static bool operator ==(Animal? animal1, Animal? animal2)
    {
        if (ReferenceEquals(animal1, animal2))
        {
            return true;
        }

        if (animal1 is null || animal2 is null)
        {
            return false;
        }

        return animal1._name == animal2._name &&
               animal1._age == animal2._age &&
               animal1._limbsCount == animal2._limbsCount &&
               animal1._type == animal2._type &&
               animal1._habitat == animal2._habitat &&
               animal1._continent == animal2._continent &&
               animal1._hasTail == animal2._hasTail;
    }

    public static bool operator !=(Animal? animal1, Animal? animal2)
    {
        return !(animal1 == animal2);
    }

    public override bool Equals(object? obj)
    {
        return obj is Animal other && this == other;
    }

    public override int GetHashCode()
    {
        return HashCode.Combine(
            _name,
            _age,
            _limbsCount,
            _type,
            _habitat,
            _continent,
            _hasTail);
    }

    public void ShowInfo()
    {
        Console.WriteLine($"Имя: {_name}");
        Console.WriteLine($"Возраст: {_age}");
        Console.WriteLine($"Количество конечностей: {_limbsCount}");
        Console.WriteLine($"Вид: {_type}");
        Console.WriteLine($"Среда обитания: {_habitat}");
        Console.WriteLine($"Континент: {_continent}");
        Console.WriteLine($"Звук: {GetSound()}");
        Console.WriteLine($"Может летать: {(CanFly() ? "да" : "нет")}");
        Console.WriteLine($"Может плавать: {(CanSwim() ? "да" : "нет")}");
        Console.WriteLine($"Есть хвост: {(ExistsTail() ? "да" : "нет")}");
    }
}
