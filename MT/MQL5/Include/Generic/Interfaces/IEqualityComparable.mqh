//+------------------------------------------------------------------+
//|                                          IEqualityComparable.mqh |
//|                             Copyright 2000-2026, MetaQuotes Ltd. |
//|                                                     www.mql5.com |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| Interface IEqualityComparable<T>.                                |
//| Usage: Defines a generalized method to create a type-specific    |
//| method for determining equality of instances.                    |
//+------------------------------------------------------------------+
template<typename T>
interface IEqualityComparable
  {
//--- method for determining equality
   bool              Equals(T value);
//--- method to calculate hash code   
   int               HashCode(void);
  };
//+------------------------------------------------------------------+
