import { MessageModel } from "./Message";
import { UserModel } from "./User";
 
export interface GroupConversationModel {
  id: string;
  name: string;
  last_message: MessageModel | null;
  admin: UserModel;
  members: UserModel | null;
}