namespace GameObjects.Interfaces
{
    public interface IAction
    {
        string Description { get; }
        int UpperLimit { get; }
        int LowerLimit { get; }
        
        bool CheckCondition(Interfaces.ICharacter player);
        bool DoAction(Interfaces.ICharacter player, Interfaces.ICharacter otherPlayer = null);
    }
}