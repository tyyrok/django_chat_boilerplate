import { UserModel } from "./User";
 
export interface GroupMessageModel {
  id: string;
  room: string;
  from_user: UserModel;
  content: string;
  timestamp: string;
  read: boolean;
}