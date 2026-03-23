//+------------------------------------------------------------------+
//|                                            IEqualityComparer.mqh |
//|                             Copyright 2000-2026, MetaQuotes Ltd. |
//|                                                     www.mql5.com |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| Interface IEqualityComparer<T>.                                  |
//| Usage: Defines methods to support the comparison of values for   |
//|        equality.                                                 |
//+------------------------------------------------------------------+
template<typename T>
interface IEqualityComparer
  {
//--- determines whether the specified values are equal
   bool      Equals(T x,T y);
//--- returns a hash code for the specified object
   int       HashCode(T value);
  };
//+------------------------------------------------------------------+
